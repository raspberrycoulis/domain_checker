import argparse
import requests
import urllib3

def check_info_php(domain, ignore_ssl=False):
    # Ensure the domain uses HTTPS; if not, prepend it.
    if not domain.startswith("https://"):
        domain = "https://" + domain
    # Construct the URL for info.php
    url = domain.rstrip("/") + "/info.php"
    try:
        if ignore_ssl:
            response = requests.get(url, timeout=5, verify=False)
        else:
            response = requests.get(url, timeout=5)
        # If status is not 404, return the URL and its status code
        if response.status_code != 404:
            return url, response.status_code
        else:
            return None, None
    except requests.RequestException as e:
        # Treat exceptions as affected since we didn't get a 404 response.
        return url, f"Error: {e}"

def load_domains(filename):
    with open(filename, 'r') as file:
        # Read non-empty lines and strip extra whitespace
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
    args = parser.parse_args()

    # If ignore_ssl flag is set, disable SSL warnings.
    if args.ignore_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    domains = load_domains(args.file)
    affected = []  # List to hold domains that do not return HTTP 404

    for domain in domains:
        url, status = check_info_php(domain, ignore_ssl=args.ignore_ssl)
        if url is not None:
            affected.append((url, status))

    if affected:
        print("Affected domains (info.php did not return HTTP 404):")
        for url, status in affected:
            print(f"{url} returned {status}")
    else:
        print("Success! No scanned domains had the info.php file present.")
