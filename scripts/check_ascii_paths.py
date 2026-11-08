#!/usr/bin/env python3
"""BLOG-017 addendum 5/6 (commander D-20261109-27, Peter D-20261109-30): fail when any path under content/ is not ASCII.

Bundle folders and file names are ASCII only (rule: src/ssot/bundle.ascii_folder); a Korean public URL is kept
with front matter `url:`. Checks every file and folder actually in the working tree under content/ — tracked,
untracked and the ones written at build time (the leftover Notion import) — not just git's list (Anton round 5 P2).
In CI it runs after the leftover import. Exit 0 = all ASCII, 1 = listed offenders, 2 = no content folder.
"""
import argparse
import os
import sys


def non_ascii(paths):
    return [p for p in paths if not p.isascii()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--root", default="content")
    args = parser.parse_args(argv)
    base = os.path.join(args.repo, args.root)
    if not os.path.isdir(base):
        print(f"check_ascii_paths: no {base}", file=sys.stderr)
        return 2
    paths = []
    for folder, dirs, files in os.walk(base):
        rel = os.path.relpath(folder, args.repo)
        paths += [os.path.join(rel, name) for name in dirs + files]
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
