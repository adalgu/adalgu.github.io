"""Built 404 page check (slot r6-P06·r13-P05·r13-P06): python scripts/check_404_page.py [public]

- public/404.html lists exactly five distinct recent posts and a home link, every link inside the built site;
- the 'finding the moved post' box is hidden in the markup and only the old-address pattern branch shows it;
- the page_not_found GA event is called exactly once, in 404.html only.
"""
import re
import sys
import urllib.parse
from pathlib import Path


def built_paths(public):
    out = set()
    for index in public.rglob("index.html"):
        rel = index.parent.relative_to(public).as_posix()
        out.add("/" if rel == "." else f"/{rel}/")
    return out


def main(argv):
    public = Path(argv[1] if len(argv) > 1 else "public")
    page = public / "404.html"
    if not page.is_file():
        print("❌ check_404_page: public/404.html missing")
        return 1
    html = page.read_text(encoding="utf-8")
    built, errors = built_paths(public), []
    section = re.search(r"data-testid=\"?not-found-recent\"?.*?</section>", html, re.S)
    hrefs = re.findall(r"href=\"?([^\"' >]+)", section.group(0)) if section else []
    paths = [urllib.parse.unquote(urllib.parse.urlparse(h).path) for h in hrefs]
    if len(paths) != 5 or len(set(paths)) != 5:
        errors.append(f"recent posts: want 5 distinct links, got {paths}")
    errors += [f"recent link not built: {p}" for p in paths if p not in built]
    home = re.search(r"<a href=\"?([^\"' >]+)\"? data-testid=\"?not-found-home", html)
    if not home or urllib.parse.urlparse(home.group(1)).path != "/":
        errors.append("home link missing")
    box = re.search(r"id=\"?redirect-info\"?[^>]*>", html)
    if not box or "display:none" not in box.group(0).replace(" ", ""):
        errors.append("redirect box is not hidden by default")
    shown = [m.start() for m in re.finditer(r"display\s*=\s*[\"']block[\"']", html)]
    tested = html.find(".test.test(")
    if not shown or tested < 0 or min(shown) < tested:
        errors.append("redirect box shown before the old-address pattern test")
    if html.count("page_not_found") != 1:
        errors.append(f"page_not_found calls in 404.html: {html.count('page_not_found')} (want 1)")
    others = [p for p in public.rglob("*.html") if p != page and "page_not_found" in p.read_text(encoding="utf-8", errors="ignore")]
    errors += [f"page_not_found outside 404: {p.relative_to(public)}" for p in others[:5]]
    for error in errors:
        print("❌ check_404_page:", error)
    if not errors:
        print(f"check_404_page: 5 recent posts + home, box hidden until a pattern matches, page_not_found once ({len(built)} pages)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
