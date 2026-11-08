#!/usr/bin/env python3
"""BLOG-017 addendum 5 (commander D-20261109-27): fail when any tracked path under content/ is not ASCII.

Bundle folders and file names are ASCII only (rule: src/ssot/bundle.ascii_folder); a Korean public URL is kept
with front matter `url:`. Reads `git ls-files -z` with quotepath off, so names are checked as they are.
Exit 0 = all ASCII, 1 = listed offenders, 2 = git failed.
"""
import argparse
import subprocess
import sys


def non_ascii(paths):
    return [p for p in paths if not p.isascii()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--root", default="content")
    args = parser.parse_args(argv)
    run = subprocess.run(["git", "-c", "core.quotepath=off", "-C", args.repo, "ls-files", "-z", "--", args.root],
                         capture_output=True)
    if run.returncode != 0:
        print(f"check_ascii_paths: git ls-files failed: {run.stderr.decode(errors='replace')[:300]}", file=sys.stderr)
        return 2
    paths = [p for p in run.stdout.decode("utf-8").split("\0") if p]
    bad = non_ascii(paths)
    for path in bad:
        print(f"check_ascii_paths: not ASCII: {path}", file=sys.stderr)
    if bad:
        print(f"check_ascii_paths: {len(bad)} of {len(paths)} paths under {args.root}/ are not ASCII — rename the "
              f"folder (scripts/ascii_bundle_folders.py) and keep the URL with front matter url:", file=sys.stderr)
        return 1
    print(f"check_ascii_paths: {len(paths)} paths under {args.root}/, all ASCII")
    return 0


if __name__ == "__main__":
    sys.exit(main())
