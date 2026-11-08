#!/usr/bin/env python3
"""One-time move: Notion flat posts -> page bundles content/posts/<slug>/index.md (BLOG-015).

Input is the flat Markdown the existing renderer (src/render.py, via
`notion_hugo_app.py --notion-only`/`--no-build`) wrote into --flat-dir. The
script never talks to Notion and never edits the body text.

For every flat post Hugo publishes (`hugo list published`, run in --site):
  - slug  = the current URL segment (written to front matter, so a later title
            change cannot move the address)
  - notion_id is kept (front matter already has it)
  - Notion-hosted images (signed, expiring URLs) are downloaded into the bundle
    and the link becomes a relative file name; external images stay as they are
Posts that would collide with an existing bundle, or whose image download
fails, are skipped and listed in the report.

Usage:
  python scripts/move_notion_posts.py --site . --flat-dir content/posts \
      --out-dir content/posts --report move_report.json [--dry-run]
"""
import argparse
import csv
import io
import json
import mimetypes
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

NOTION_IMAGE_HOSTS = (
    "prod-files-secure.s3.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
    "file.notion.so",
)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")
EXT_BY_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
}


def is_notion_image(url):
    host = urllib.parse.urlsplit(url).hostname or ""
    return host in NOTION_IMAGE_HOSTS or host.endswith(".notion-static.com")


def published_flat_pages(site, flat_dir):
    out = subprocess.run(["hugo", "list", "published"], cwd=site, capture_output=True, text=True, check=True).stdout
    rows = list(csv.DictReader(io.StringIO(out)))
    flat_prefix = os.path.normpath(flat_dir) + os.sep
    pages = []
    for r in rows:
        path = os.path.normpath(r["path"])
        if r["kind"] != "page" or not path.startswith(flat_prefix):
            continue
        if os.sep in path[len(flat_prefix):]:  # already a bundle
            continue
        pages.append(r)
    return pages


def url_segment(permalink):
    path = urllib.parse.unquote(urllib.parse.urlsplit(permalink).path)
    parts = [p for p in path.split("/") if p]
    if len(parts) != 2 or parts[0] != "posts":
        raise ValueError(f"unexpected permalink {permalink}")
    return parts[1]


def split_front_matter(text):
    if not text.startswith("---\n"):
        raise ValueError("no front matter")
    end = text.index("\n---\n", 4)
    return text[4:end + 1], text[end + 5:]


def set_slug(front, slug):
    """Set `slug:` in YAML front matter text without re-dumping (other keys byte-identical)."""
    line = f"slug: {json.dumps(slug, ensure_ascii=False)}\n"
    lines = front.splitlines(keepends=True)
    out, replaced, i = [], False, 0
    while i < len(lines):
        if lines[i].startswith("slug:"):
            out.append(line)
            replaced = True
            i += 1
            while i < len(lines) and lines[i].startswith((" ", "\t")):  # folded continuation
                i += 1
            continue
        out.append(lines[i])
        i += 1
    if not replaced:
        out.append(line)
    return "".join(out)


def download(url, dest_dir, index):
    req = urllib.request.Request(url, headers={"User-Agent": "move-notion-posts/1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        ctype = (resp.headers.get_content_type() or "").lower()
    ext = EXT_BY_TYPE.get(ctype) or os.path.splitext(urllib.parse.urlsplit(url).path)[1].lower() \
        or mimetypes.guess_extension(ctype) or ".bin"
    name = f"image-{index:02d}{ext}"
    with open(os.path.join(dest_dir, name), "wb") as f:
        f.write(data)
    return name, len(data)


def move_one(page, site, out_dir, dry_run):
    src = os.path.join(site, page["path"])
    slug = url_segment(page["permalink"])
    with open(src, encoding="utf-8") as f:
        text = f.read()
    front, body = split_front_matter(text)
    notion_id = re.search(r"^notion_id:\s*(\S+)", front, re.M)
    rec = {"source": page["path"], "slug": slug, "title": page["title"],
           "notion_id": notion_id.group(1) if notion_id else "", "notion_images": 0,
           "external_images": 0, "bytes": 0, "status": "moved"}
    if not rec["notion_id"]:
        rec["status"] = "skipped: no notion_id"
        return rec
    dest = os.path.join(out_dir, slug)
    if os.path.exists(dest):
        rec["status"] = "skipped: bundle exists"
        return rec

    urls = [m.group(2) for m in IMAGE_RE.finditer(body)]
    notion_urls = list(dict.fromkeys(u for u in urls if is_notion_image(u)))
    rec["external_images"] = sum(1 for u in urls if not is_notion_image(u))
    if dry_run:
        rec["notion_images"] = len(notion_urls)
        rec["status"] = "dry-run"
        return rec

    os.makedirs(dest)
    names = {}
    try:
        for i, u in enumerate(notion_urls, 1):
            names[u], size = download(u, dest, i)
            rec["bytes"] += size
    except Exception as e:  # leave nothing half-moved
        for n in os.listdir(dest):
            os.remove(os.path.join(dest, n))
        os.rmdir(dest)
        rec["status"] = f"skipped: image download failed ({type(e).__name__})"
        return rec
    rec["notion_images"] = len(names)

    body = IMAGE_RE.sub(lambda m: f"![{m.group(1)}]({names.get(m.group(2), m.group(2))})", body)
    with open(os.path.join(dest, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"---\n{set_slug(front, slug)}---\n{body}")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", default=".", help="Hugo site root holding the flat posts")
    ap.add_argument("--flat-dir", default="content/posts", help="flat post folder, relative to --site")
    ap.add_argument("--out-dir", default="content/posts", help="bundle output folder")
    ap.add_argument("--report", help="write a JSON report here")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = args.out_dir if os.path.isabs(args.out_dir) else os.path.join(args.site, args.out_dir)
    pages = published_flat_pages(args.site, args.flat_dir)
    seen, records = {}, []
    for p in pages:
        slug = url_segment(p["permalink"])
        if slug in seen:
            records.append({"source": p["path"], "slug": slug, "status": f"skipped: same slug as {seen[slug]}"})
            continue
        seen[slug] = p["path"]
        records.append(move_one(p, args.site, out_dir, args.dry_run))

    moved = [r for r in records if r["status"] in ("moved", "dry-run")]
    summary = {"published_flat": len(pages), "moved": len(moved),
               "skipped": [r for r in records if r not in moved],
               "notion_images": sum(r.get("notion_images", 0) for r in moved),
               "external_images": sum(r.get("external_images", 0) for r in moved),
               "bytes": sum(r.get("bytes", 0) for r in moved)}
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "posts": records}, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "skipped"}, ensure_ascii=False),
          "skipped", len(summary["skipped"]))
    return 0 if not summary["skipped"] else 1


if __name__ == "__main__":
    sys.exit(main())
