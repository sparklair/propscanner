import hashlib
import re
from urllib.parse import urlparse, urlunparse

from colorama import Fore, just_fix_windows_console


just_fix_windows_console()


def normalize_url(url):
    parsed = urlparse(url.strip())

    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    path = parsed.path or "/"

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))


def same_origin(url, base):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base)

    return (
        parsed_url.scheme in {"http", "https"}
        and parsed_url.scheme == parsed_base.scheme
        and parsed_url.netloc == parsed_base.netloc
    )


def build_url(url, payload):
    parsed = urlparse(url)
    query = parsed.query

    if query:
        query = f"{query}&{payload}"
    else:
        query = payload

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path or "/",
        parsed.params,
        query,
        parsed.fragment,
    ))


def finding_filename(url):
    parsed = urlparse(url)
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "_", parsed.netloc + parsed.path).strip("_")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]

    return f"{slug or 'target'}_{digest}.txt"


def info(msg):
    print(f"{Fore.CYAN}[*]{Fore.RESET} {msg}")


def good(msg):
    print(f"{Fore.GREEN}[+]{Fore.RESET} {msg}")


def bad(msg):
    print(f"{Fore.RED}[-]{Fore.RESET} {msg}")


def warn(msg):
    print(f"{Fore.YELLOW}[!]{Fore.RESET} {msg}")
