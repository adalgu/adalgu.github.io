#!/usr/bin/env python3
"""Check every published English post against its Korean original.

For each content/posts/<bundle>/index.en.md with draft false:
- paragraph, heading, link and image counts equal the Korean index.md
- both files carry the same translationKey
- no Korean left outside parentheses, code and URLs (lines are listed)

    python3 scripts/check_en_parity.py [bundle ...]

Exit 1 on any mismatch. Counting rules follow the TASK-615 draft check.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

POSTS = Path(__file__).resolve().parent.parent / "content" / "posts"
HANGUL = re.compile(r"[가-힣]")


def split(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    return (match.group(1), text[match.end():]) if match else ("", text)


def field(front: str, name: str) -> str:
    match = re.search(rf"^{name}:\s*(.*)$", front, re.M)
    return match.group(1).strip().strip("'\"") if match else ""


def blocks(md: str) -> list[str]:
    out, cur, fence = [], [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
        if not fence and not line.strip():
            if cur:
                out.append("\n".join(cur))
                cur = []
        else:
            cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def stats(md: str) -> dict[str, int]:
    nocode = re.sub(r"```.*?```", "", md, flags=re.S)
    return {
        "paragraphs": len(blocks(md)),
        "headings": len(re.findall(r"^#{1,6} ", nocode, re.M)),
        "links": len(re.findall(r"(?<!!)\[[^\]]*\]\([^)]+\)", nocode)) + len(re.findall(r"\{\{<\s*relref", nocode)),
        "images": len(re.findall(r"!\[[^\]]*\]\([^)]+\)", nocode)) + len(re.findall(r"\{\{<\s*figure", nocode)),
    }


def korean_lines(md: str) -> list[str]:
    out, fence = [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence or line.lstrip().startswith("{{<"):  # shortcodes cite Korean sources by their own titles
            continue
        bare = re.sub(r"`[^`]*`", "", line)
        bare = re.sub(r"\]\([^)]*\)", "]", bare)
        bare = re.sub(r"https?://\S+", "", bare)
        while re.search(r"\([^()]*\)", bare):  # Korean original in parentheses is allowed, nested too
            bare = re.sub(r"\([^()]*\)", "", bare)
        if HANGUL.search(bare):
            out.append(line.strip()[:100])
    return out


def check(bundle: Path) -> list[str]:
    en_front, en_body = split((bundle / "index.en.md").read_text(encoding="utf-8"))
    ko_front, ko_body = split((bundle / "index.md").read_text(encoding="utf-8"))
    problems = []
    key_en, key_ko = field(en_front, "translationKey"), field(ko_front, "translationKey")
    if not key_en or key_en != key_ko:
        problems.append(f"translationKey en={key_en!r} ko={key_ko!r}")
    a, b = stats(ko_body), stats(en_body)
    for name in a:
        if a[name] != b[name]:
            problems.append(f"{name} ko={a[name]} en={b[name]}")
    for line in korean_lines(en_body):
        problems.append(f"korean: {line}")
    if HANGUL.search(field(en_front, "title") + field(en_front, "description")):
        problems.append("korean in title/description")
    return problems


def main(argv: list[str]) -> int:
    bundles = [POSTS / name for name in argv] if argv else sorted(p.parent for p in POSTS.glob("*/index.en.md"))
    failed = checked = 0
    for bundle in bundles:
        front, _ = split((bundle / "index.en.md").read_text(encoding="utf-8"))
        if field(front, "draft") == "true":
            continue
        checked += 1
        problems = check(bundle)
        if problems:
            failed += 1
            print(f"FAIL {bundle.name}")
            for problem in problems:
                print(f"  {problem}")
    print(f"check_en_parity: {checked} English posts, {failed} with problems")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
