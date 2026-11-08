"""Post bundles (content/posts/<slug>/index.md + files) and the content hash both sides agree on."""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

INDEX = "index.md"


@dataclass
class Bundle:
    slug: str
    path: Path
    meta: dict
    front: str  # front matter text as written (kept verbatim when the metadata does not change)
    body: str
    files: dict = field(default_factory=dict)  # name -> sha256 of every other file in the bundle

    @property
    def hash(self):
        return content_hash(self.meta, self.body, self.files)


ASCII_FOLDER = re.compile(r"[a-z0-9][a-z0-9-]*")


def ascii_folder(candidate, date, notion_id=""):
    """The one naming rule for bundle folders (BLOG-017 addendum 5, commander D-20261109-27): folders are ASCII
    only. A lowercase a-z/0-9/- candidate (an ASCII Notion Slug) is used as it is; anything else becomes
    post-<YYYYMMDD>-<first 8 of the Notion id> (or of a hash of the candidate). The public URL is not the folder:
    a front matter `url:` keeps it."""
    candidate = str(candidate or "").strip().lower()
    if ASCII_FOLDER.fullmatch(candidate) and not candidate.endswith("-"):
        return candidate
    day = re.sub(r"[^0-9]", "", str(date or ""))[:8] or "00000000"
    tail = re.sub(r"[^0-9a-f]", "", str(notion_id or "").lower())[:8] or hashlib.sha256(candidate.encode()).hexdigest()[:8]
    return f"post-{day}-{tail}"


def normalize_body(body):
    return "\n".join(line.rstrip() for line in body.strip().splitlines())


def content_hash(meta, body, files):
    canon = json.dumps({"meta": meta, "body": normalize_body(body), "files": dict(sorted(files.items()))},
                       sort_keys=True, ensure_ascii=False, default=str)
    return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()


def file_hashes(path, extra=None):
    out = {}
    for item in sorted(Path(path).iterdir()) if Path(path).is_dir() else []:
        if item.is_file() and item.name != INDEX and not item.name.startswith("."):
            out[item.name] = hashlib.sha256(item.read_bytes()).hexdigest()
    for name, data in (extra or {}).items():
        out[name] = hashlib.sha256(data).hexdigest()
    return out


def split_front(raw):
    if not raw.startswith("---"):
        return None
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1], parts[2].lstrip("\n")


def read_bundle(path):
    path = Path(path)
    index = path / INDEX
    if not index.is_file():
        return None
    split = split_front(index.read_text(encoding="utf-8"))
    if not split:
        return None
    front, body = split
    meta = yaml.safe_load(front) or {}
    return Bundle(slug=path.name, path=path, meta=meta, front=front, body=body, files=file_hashes(path))


def all_bundles(posts_dir):
    out = []
    for index in sorted(Path(posts_dir).glob(f"*/{INDEX}")):
        bundle = read_bundle(index.parent)
        if bundle:
            out.append(bundle)
    return out


def render_index(bundle, meta, body):
    """index.md text. Front matter kept byte for byte when meta is unchanged (no quoting churn in diffs)."""
    front = bundle.front if meta == bundle.meta else "\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    body = body if body.endswith("\n") else body + "\n"
    return f"---{front}---\n\n{body}"
