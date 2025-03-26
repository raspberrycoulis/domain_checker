import argparse
import requests
import urllib3
import sys
import time
import os

def check_info_php(domain, ignore_ssl=False, follow_redirects=False):
    """
    Check the /info.php URL for the given domain.

    Returns:
      - (url, status, None) if the GET request is successful and returns a status code other than 404.
      - (url, None, error_message) if an exception occurs during the GET request.
      - (None, None, None) if the response status code is 404 (i.e., desired response).
    """
    if not domain.startswith("https://"):
        domain = "https://" + domain
    url = domain.rstrip("/") + "/info.php"
    try:
        response = requests.get(
            url,
            timeout=5,
            verify=(not ignore_ssl),
            allow_redirects=follow_redirects
        )
        if response.status_code != 404:
            return url, response.status_code, None
        else:
            return None, None, None
    except requests.RequestException as e:
        return url, None, str(e)

def load_domains(filename):
    """Load and return a list of domains from the given file, one per line."""
    with open(filename, 'r') as file:
        domains = [line.strip() for line in file if line.strip()]
    return domains

def send_webhook_notification(urgent_list, redirected_list, webhook_url):
    """
    Send a webhook notification to the specified Teams webhook URL using an Adaptive Card.
    The payload includes a top-level "summary" and an "attachments" array for Teams.
    """
    # Build a multi-line string with domain details.
    domain_details = "\n".join([f"[{url}]({url})\n" for url, status in urgent_list])
    redirect_details = "\n".join([f"[{url}]({url})\n" for url, status in redirected_list])
    
    # Construct the Adaptive Card content.
    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.6",
        "body": [
            {
                "type": "TextBlock",
                "size": "ExtraLarge",
                "weight": "Bolder",
                "text": "Possible exposed credentials!",
                "style": "heading",
                "color": "Attention"
            },
            {
                "type": "TextBlock",
                "text": "The following domains may have an `info.php` file exposed and require **urgent** attention:",
                "wrap": True,
                "separator": True
            },
            {
                "type": "TextBlock",
                "text": domain_details,
                "wrap": True,
                "separator": True
            },
            {
                "type": "TextBlock",
                "text": "**The following domains redirected, so are worth checking:**",
                "wrap": True,
                "spacing": "ExtraLarge",
                "separator": True
            },
            {
                "type": "TextBlock",
                "text": redirect_details,
                "wrap": True,
                "separator": True
            }
        ]
    }
    
    # Wrap the Adaptive Card in a Teams-compatible payload.
    payload = {
        "summary": "Possible exposed credentials",
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": adaptive_card
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code != 200:
            print("Failed to send webhook notification.")
            print("Response:", response.text)
        else:
            print("Webhook notification sent successfully.")
    except requests.RequestException as e:
        print("Error sending webhook notification:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check domains for /info.php and report those that do not return HTTP 404."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default="domains.txt",
        help="Path to the file containing domains (one per line). Default is domains.txt."
    )
    parser.add_argument(
        "--ignore-ssl",
        action="store_true",
        help="Ignore SSL warnings and disable SSL certificate verification."
    )
    parser.add_argument(
        "--follow-redirects",
        action="store_true",
        help="Follow redirects when checking the /info.php URL. By default, redirects are not followed."
    )
    parser.add_argument(
        "--check-subdomains",
        action="store_true",
        help="Also check sub-domains listed in sub-domains.txt."
    )
    parser.add_argument(
        "--webhook-url",
        type=str,
        help="URL of the webhook to send urgent domain notifications (e.g., Teams webhook URL)."
    )
    args = parser.parse_args()

    # Disable SSL warnings if the flag is set.
    if args.ignore_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Load main domains.
    domains = load_domains(args.file)

    # If sub-domains flag is enabled, load additional sub-domains.
    if args.check_subdomains:
        if os.path.exists("sub-domains.txt"):
            sub_domains = load_domains("sub-domains.txt")
            domains.extend(sub_domains)
            print(f"Additionally, found {len(sub_domains)} sub-domains to check.")
        else:
            print("Sub-domains file 'sub-domains.txt' not found; skipping sub-domain checks.")

    total_domains = len(domains)

    # Lists for grouping responses.
    urgent = []         # HTTP 200 – requires urgent attention.
    redirected = []     # HTTP 301, 302, 307, 308 – redirected.
    server_errors = []  # HTTP 500, 503 – server issues.
    others = []         # Other non-404 responses.
    errors = []         # Request errors.

    for domain in domains:
        url, status, error = check_info_php(
            domain, 
            ignore_ssl=args.ignore_ssl, 
            follow_redirects=args.follow_redirects
        )
        if url is not None:
            if error:
                errors.append((url, error))
            else:
                if status == 200:
                    urgent.append((url, status))
                elif status in [301, 302, 307, 308]:
                    redirected.append((url, status))
                elif status in [500, 503]:
                    server_errors.append((url, status))
                else:
                    others.append((url, status))

    # Output results in separate blocks.
    if urgent:
        print("\nThe following domain(s) responded with a HTTP 200 status code, so need checking urgently:\n")
        for url, status in urgent:
            print(f"{url}")

    if redirected:
        print("\nThe following domain(s) redirected and are probably fine:\n")
        for url, status in redirected:
            print(f"{url} returned status code {status}")

    if server_errors:
        print("\nThere may have been an issue with the following domain(s):\n")
        for url, status in server_errors:
            print(f"{url} - returned HTTP {status}")

    if others:
        print("\nThe following domain(s) returned other status codes:\n")
        for url, status in others:
            print(f"{url} - returned HTTP {status}")

    if errors:
        print("\nThe script completed, but the following issues were found:\n")
        for url, error in errors:
            print(f"{url}: {error}")

    # If urgent domains were found and a webhook URL is provided, send a webhook notification.
    if urgent and args.webhook_url:
        send_webhook_notification(urgent, redirected, args.webhook_url)