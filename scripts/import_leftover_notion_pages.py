#!/usr/bin/env python3
"""BLOG-017 F1: import only the Notion pages listed in config/notion_leftover_pages.txt as flat posts.

Replaces the old whole-DB Notion -> Hugo import (hourly, cached content/posts, orphan cleanup that removes
files). Every other post is a repo bundle. A listed page that now has a bundle with the same notion_id or slug is
skipped (render.save_page), and scripts/check_duplicate_urls.py stops the build on any URL twice.
Exit 1 when a listed page cannot be imported (its URL would vanish from the site).
The flat file gets an ASCII name by the bundle folder rule (src/ssot/bundle.ascii_folder) — the old importer named
it after the title (Korean), which the build's ASCII path check stops (BLOG-017 addendum 6). The URL comes from
the front matter slug, so the file name does not change it.
Key: NOTION_TOKEN or NOTION_API_KEY.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LIST = ROOT / "config" / "notion_leftover_pages.txt"
CONFIG = {"filename": {"format": "date-title", "date_format": "%Y-%m-%d", "korean_title": "slug"}}


def page_ids(path=LIST):
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def main(argv=None, notion=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", default=str(LIST))
    args = parser.parse_args(argv)
    from src.render import get_page_properties, save_page
    from src.ssot.bundle import ascii_folder
    from src.utils.file_utils import get_filename_with_extension
    ids = page_ids(args.list)
    if not ids:
        print("leftover: nothing listed")
        return 0
    if notion is None:
        token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not token:
            print("leftover: no Notion key (NOTION_TOKEN or NOTION_API_KEY)", file=sys.stderr)
            return 1
        from src.notion_retry import RetryingClient
        notion = RetryingClient(auth=token)
    failed = 0
    for page_id in ids:
        try:
            page = notion.pages.retrieve(page_id=page_id)
        except Exception as error:
            print(f"leftover: {page_id} not readable ({type(error).__name__})", file=sys.stderr)
            failed += 1
            continue
        content = save_page(page, notion, "posts", CONFIG)
        if content is None:
            print(f"leftover: {page_id} failed to render", file=sys.stderr)
            failed += 1
            continue
        if content:
            props = get_page_properties(page)
            written = Path("content/posts") / get_filename_with_extension(props, page["id"], CONFIG["filename"])
            ascii_name = written.with_name(ascii_folder(props.get("slug"), props.get("date"), page["id"]) + ".md")
            if written != ascii_name and written.exists():
                written.rename(ascii_name)
            print(f"leftover: {page_id} imported as {ascii_name.name}")
        else:
            print(f"leftover: {page_id} skipped (repo bundle or skipRendering)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
