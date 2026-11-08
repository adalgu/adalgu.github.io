#!/usr/bin/env python3
"""BLOG-017 F1: fail the build when two published pages share one URL.

Replaces check_flat_posts.sh (which counted Notion flat files as the success condition). Every post is a repo
bundle now; a leftover flat copy or a second bundle with the same slug makes two pages at one URL — Hugo
builds them both silently and the site shows whichever wins.

    python scripts/check_duplicate_urls.py                 # runs `hugo list published` here
    python scripts/check_duplicate_urls.py --csv list.csv  # same check on a saved listing (tests)
Exit 0 = every URL once, 1 = duplicates (listed), 2 = could not list.
"""
import argparse
import collections
import csv
import io
import subprocess
import sys


def duplicates(listing):
    rows = list(csv.DictReader(io.StringIO(listing)))
    counts = collections.Counter(row["permalink"] for row in rows if row.get("kind") == "page")
    return rows, {url: n for url, n in counts.items() if n > 1}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", help="saved `hugo list published` output instead of running hugo")
    parser.add_argument("--hugo", default="hugo")
    args, extra = parser.parse_known_args(argv)
    if args.csv:
        listing = open(args.csv, encoding="utf-8").read()
    else:
        run = subprocess.run([args.hugo, "list", "published", *extra], capture_output=True, text=True)
        if run.returncode != 0:
            print(f"check_duplicate_urls: hugo list failed: {run.stderr.strip()[:500]}", file=sys.stderr)
            return 2
        listing = run.stdout
    rows, dup = duplicates(listing)
    pages = sum(1 for row in rows if row.get("kind") == "page")
    if dup:
        for url, n in sorted(dup.items()):
            print(f"check_duplicate_urls: {n} pages at {url}", file=sys.stderr)
        print(f"check_duplicate_urls: {len(dup)} duplicated URLs among {pages} pages — build stopped", file=sys.stderr)
        return 1
    print(f"check_duplicate_urls: {pages} pages, every URL once")
    return 0


if __name__ == "__main__":
    sys.exit(main())
