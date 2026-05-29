import argparse
import asyncio
import sys

from scanner import PrototypePollutionScanner
from utils import bad, normalize_url


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prototype pollution scanner for authorized bug bounty testing."
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("-u", "--url", help="Single target URL")
    target_group.add_argument("-f", "--file", help="File with target URLs")

    parser.add_argument("--crawl", action="store_true", help="Crawl same-origin links")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum crawled pages per target")
    parser.add_argument("-c", "--concurrency", type=int, default=3, help="Concurrent browser checks")
    parser.add_argument("--timeout", type=int, default=15000, help="Navigation timeout in milliseconds")

    return parser.parse_args()


def load_targets(args):
    raw_targets = []

    if args.url:
        raw_targets.append(args.url)

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            raw_targets.extend(
                line.strip()
                for line in f
                if line.strip() and not line.lstrip().startswith("#")
            )

    targets = []

    for target in raw_targets:
        try:
            targets.append(normalize_url(target))
        except ValueError as exc:
            bad(str(exc))

    return list(dict.fromkeys(targets))


async def main():
    args = parse_args()
    targets = load_targets(args)

    if not targets:
        bad("No valid targets to scan.")
        return 1

    scanner = PrototypePollutionScanner(
        targets=targets,
        crawl=args.crawl,
        max_pages=max(args.max_pages, 0),
        concurrency=max(args.concurrency, 1),
        timeout=max(args.timeout, 1000),
    )

    await scanner.run()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
