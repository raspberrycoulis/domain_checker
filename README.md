# Domain checker
This Python scripts runs through a defined list of domains, specified in the `domains.txt` file and checks whether a file called `info.php` is present. The desired outcome is that the file **does not** exist, which returns a `HTTP 404` status code. 

Update the `domains.txt` file to specify a list of domains you want the script to check.

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

