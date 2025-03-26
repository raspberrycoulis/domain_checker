# Domain checker
This Python scripts runs through a defined list of domains, specified in the `domains.txt` file and checks whether a file called `info.php` is present. The desired outcome is that the file **does not** exist, which returns a `HTTP 404` status code. 

Update the `domains.txt` file to specify a list of domains you want the script to check. If you want to also check sub-domains, ensure they are specified in the `sub-domains.txt` file and the `--check-subdomains` flag is used (see below for examples).

## Usage
Run simply by calling:

```bash
python3 domain_checker.py
```

To specify a different list of domains, other than the default `domains.txt`:
```bash
python3 domain_checker.py --file mylist.txt
```

To ignore SSL checks:
```bash
python3 domain_checker.py --ignore-ssl
```

To follow redirects:
```bash
python3 domain_checker.py --follow-redirects
```

To check sub-subdomains - this requires the `sub-domains.txt` file to include a list of sub-domains to check as well:
```bash
python3 domain_checker.py --check-subdomains
```

To send Teams notifications via webhook, include the webhook URL as follows:
```bash
python3 domain_checker.py --webhook-url "https://add_webhook_url_here"

## Web UI
There is also a web UI included in this, done via a Flask app, which allows you to run the script via a browser. To do this, the base app shuold be running, which can be started manually by running:

```bash
python3 app.py
```

Then you can visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser. There is a self-explanatory front-end where the same options can be applied before running the check.