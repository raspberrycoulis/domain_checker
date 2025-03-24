import argparse
import requests
import urllib3
import sys
import time

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
    args = parser.parse_args()

    # If ignore_ssl flag is set, disable SSL warnings.
    if args.ignore_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    domains = load_domains(args.file)
    total_domains = len(domains)

    # Print a message before processing begins.
    print(f"\nThere are {total_domains} domains to be checked.")
    print("\nPlease wait whilst I check for you...\n")

    affected = []  # To hold (url, status) for domains that didn't return 404.
    errors = []    # To hold (url, error message) for any errors encountered.

    spinner_chars = ["|", "/", "-", "\\"]
    for i, domain in enumerate(domains, start=1):
        url, status, error = check_info_php(domain, ignore_ssl=args.ignore_ssl, follow_redirects=args.follow_redirects)
        if url is not None:
            if error:
                errors.append((url, error))
            else:
                affected.append((url, status))
        # Update progress
        progress_percent = (i / total_domains) * 100
        spinner = spinner_chars[i % len(spinner_chars)]
        progress_message = f"Progress: {progress_percent:.0f}% of domains checked {spinner}"
        # Write progress message to the same line.
        sys.stdout.write("\r" + progress_message)
        sys.stdout.flush()
        # Optional: small delay to make spinner more visible, remove if not needed.
        time.sleep(0.05)
    # Ensure we move to a new line after progress.
    print()

    if affected:
        print("\nThe following domains may have an info.php file present and need to be manually checked:\n")
        for url, status in affected:
            print(f"{url} returned status code {status}")
    else:
        print("All domains returned HTTP 404 for /info.php.")

    if errors:
        print("\nThe script completed, but the following issues were found:\n")
        for url, error in errors:
            print(f"{url}: {error}")
