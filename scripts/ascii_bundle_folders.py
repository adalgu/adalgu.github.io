#!/usr/bin/env python3
"""BLOG-017 addendum 5 (commander D-20261109-27): rename non-ASCII bundle folders to ASCII ones, URL unchanged.

For each content/posts/<folder>/ whose name is not ASCII:
  new folder = src.ssot.bundle.ascii_folder(slug, date, notion_id)  (the one naming rule)
  git mv old new (the bundle's files move with it)
  front matter: the `slug:` line becomes `url: "/posts/<old>/"` — the public URL stays exactly what it is
Dry run by default (prints the table); --apply does it. Running it again finds nothing to do.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ssot.bundle import all_bundles, ascii_folder  # noqa: E402


def plan(repo):
    rows = []
    for bundle in all_bundles(Path(repo) / "content" / "posts"):
        if bundle.slug.isascii():
            continue
        meta = bundle.meta
        old_path = str(meta.get("url") or f"/posts/{meta.get('slug') or bundle.slug}/")
        new = ascii_folder(meta.get("slug") or bundle.slug, meta.get("date"), meta.get("notion_id"))
        rows.append({"old": bundle.slug, "new": new, "url": old_path, "path": bundle.path})
    news = [r["new"] for r in rows]
    taken = {p.name for p in (Path(repo) / "content" / "posts").iterdir()}
    clash = [n for n in news if news.count(n) > 1 or n in taken]
    if clash:
        raise SystemExit(f"ascii_bundle_folders: name clash {sorted(set(clash))} — nothing moved")
    return rows


def front_with_url(text, url):
    head, sep, body = text.partition("\n---\n")
    lines = head.split("\n")
    url_line = f'url: "{url}"'
    if any(line.startswith("url:") for line in lines):
        return text
    for i, line in enumerate(lines):
        if line.startswith("slug:"):
            lines[i] = url_line
            break
    else:
        lines.insert(1, url_line)
    return "\n".join(lines) + sep + body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    rows = plan(args.repo)
    print("| old folder | new folder | public URL (unchanged) |\n|---|---|---|")
    for r in rows:
        print(f"| {r['old']} | {r['new']} | {r['url']} |")
    if not args.apply:
        print(f"ascii_bundle_folders: {len(rows)} to rename (dry-run)")
        return 0
    for r in rows:
        subprocess.run(["git", "-C", args.repo, "mv", f"content/posts/{r['old']}", f"content/posts/{r['new']}"], check=True)
        index = Path(args.repo) / "content" / "posts" / r["new"] / "index.md"
        index.write_text(front_with_url(index.read_text(encoding="utf-8"), r["url"]), encoding="utf-8")
    print(f"ascii_bundle_folders: {len(rows)} renamed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
