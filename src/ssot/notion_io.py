"""Thin Notion layer for the sync engine.

Every call goes through Client.request with a pinned API version, so the engine works the same on
notion-client 2.x before and after the 2025-09 data-source API. Every list is read to the end
(has_more / next_cursor) — a page holds 100 children per response.
"""
import os

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100
APPEND_LIMIT = 100


class NotionIO:
    def __init__(self, client):
        self.client = client
        self._user_types = {}
        self._me = None

    @classmethod
    def from_env(cls):
        token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not token:
            raise SystemExit("ssot: no Notion key (NOTION_TOKEN or NOTION_API_KEY)")
        try:
            from ..notion_retry import RetryingClient as Client
        except ImportError:  # pragma: no cover - layout without the retrying client
            from notion_client import Client
        return cls(Client(auth=token, notion_version=NOTION_VERSION))

    def _call(self, path, method, query=None, body=None):
        return self.client.request(path=path, method=method, query=query, body=body)

    def _paged(self, path, method, body=None):
        cursor = None
        while True:
            page = {"page_size": PAGE_SIZE}
            if cursor:
                page["start_cursor"] = cursor
            if method == "GET":
                found = self._call(path, "GET", query=page)
            else:
                found = self._call(path, method, body={**(body or {}), **page})
            yield from found.get("results", [])
            cursor = found.get("next_cursor")
            if not found.get("has_more") or not cursor:
                return

    # databases
    def database(self, database_id):
        return self._call(f"databases/{database_id}", "GET")

    def add_property(self, database_id, name, spec):
        """Adds one column. Never removes or renames one."""
        return self._call(f"databases/{database_id}", "PATCH", body={"properties": {name: spec}})

    def query(self, database_id, filter=None):
        return [self._with_editor(p) for p in
                self._paged(f"databases/{database_id}/query", "POST", body={"filter": filter} if filter else {})]

    # users: a page's last_edited_by holds only {object, id}; the engine needs to know bot or person
    def user_type(self, user_id):
        if user_id not in self._user_types:
            try:
                self._user_types[user_id] = self._call(f"users/{user_id}", "GET").get("type") or "person"
            except Exception:  # no user-information capability: only our own id is known to be a bot
                if self._me is None:
                    self._me = self._call("users/me", "GET").get("id")
                self._user_types[user_id] = "bot" if user_id == self._me else "person"
        return self._user_types[user_id]

    def _with_editor(self, page):
        editor = page.get("last_edited_by") or {}
        if editor.get("id") and "type" not in editor:
            editor["type"] = self.user_type(editor["id"])
        return page

    # pages
    def page(self, page_id):
        return self._with_editor(self._call(f"pages/{page_id}", "GET"))

    def create_page(self, database_id, properties, cover=None):
        body = {"parent": {"database_id": database_id}, "properties": properties}
        if cover:
            body["cover"] = cover
        return self._call("pages", "POST", body=body)

    def update_page(self, page_id, properties=None, cover=None):
        body = {}
        if properties:
            body["properties"] = properties
        if cover:
            body["cover"] = cover
        return self._call(f"pages/{page_id}", "PATCH", body=body)

    # blocks
    def children(self, block_id):
        return list(self._paged(f"blocks/{block_id}/children", "GET"))

    def delete_block(self, block_id):
        return self._call(f"blocks/{block_id}", "DELETE")

    def append(self, block_id, children):
        created = []
        for at in range(0, len(children), APPEND_LIMIT):
            found = self._call(f"blocks/{block_id}/children", "PATCH", body={"children": children[at:at + APPEND_LIMIT]})
            created += (found or {}).get("results", []) if isinstance(found, dict) else []
        return created

    def tree(self, block_id):
        """The blocks under block_id with their children (key _children), read to the end."""
        out = []
        for block in self.children(block_id):
            if block.get("has_children") and block["type"] not in ("child_page", "child_database"):
                block = dict(block, _children=self.tree(block["id"]))
            out.append(block)
        return out

    def append_staged(self, block_id, blocks):
        """Append level by level (each block, then its children under the new id), so no request nests deeper than
        Notion allows. Used to put an old body back."""
        flat = [{k: v for k, v in b.items() if k != "_kids"} for b in blocks]
        created = self.append(block_id, flat)
        for made, block in zip(created, blocks):
            if block.get("_kids"):
                self.append_staged(made["id"], block["_kids"])

    def replace_children(self, block_id, children, rounds=3):
        """Old body out, new body in — atomically as far as the API allows (BLOG-017 addendum 9): the old blocks are
        read first and kept in memory; if adding the new body fails, whatever got added is removed and the old body
        is put back, then the error is raised. Callers validate the new body before calling (engine.invalid_reasons)."""
        old_tree = self.tree(block_id)
        for _ in range(rounds):
            old = self.children(block_id)
            if not old:
                break
            for item in old:
                self.delete_block(item["id"])
        else:
            if self.children(block_id):
                raise RuntimeError(f"ssot: {block_id} still has old blocks after {rounds} rounds — new body not appended")
        try:
            self.append(block_id, children)
        except Exception:
            for item in self.children(block_id):
                self.delete_block(item["id"])
            self.append_staged(block_id, [writable(b) for b in old_tree if writable(b)])
            raise


READ_ONLY = {"id", "object", "created_time", "last_edited_time", "created_by", "last_edited_by", "has_children",
             "archived", "in_trash", "parent", "_children"}
CANNOT_CREATE = {"child_page", "child_database", "unsupported", "link_preview", "synced_block", "template", "ai_block"}


def _writable_text(items):
    out = []
    for item in items or []:
        kind = item.get("type", "text")
        piece = {"type": kind, kind: item.get(kind) or {"content": item.get("plain_text", "")}}
        if kind == "text" and item.get("href") and not (piece["text"] or {}).get("link"):
            piece["text"] = dict(piece["text"], link={"url": item["href"]})
        marks = {k: v for k, v in (item.get("annotations") or {}).items() if v and k != "color"}
        if marks:
            piece["annotations"] = marks
        out.append(piece)
    return out


def writable(block):
    """A block as read → the same block as a create request (children under _kids for append_staged). None when the
    API cannot create that kind. A Notion-hosted file (signed URL) goes back as an external link to it."""
    kind = block.get("type")
    if kind in CANNOT_CREATE:
        return None
    data = {k: v for k, v in (block.get(kind) or {}).items() if k not in READ_ONLY}
    for key in ("rich_text", "caption"):
        if key in data:
            data[key] = _writable_text(data[key])
    if "cells" in data:
        data["cells"] = [_writable_text(cell) for cell in data["cells"]]
    if data.get("type") == "file" and isinstance(data.get("file"), dict):
        data = dict(data, type="external", external={"url": data["file"].get("url", "")})
        data.pop("file", None)
    out = {"object": "block", "type": kind, kind: data}
    kids = [w for w in (writable(c) for c in block.get("_children") or []) if w]
    if kind == "table":  # Notion wants a table's rows with the table
        data["children"] = kids
    elif kind == "column_list":  # and columns (each with at least one child) with the column list
        data["children"] = [dict(c, column=dict(c["column"], children=[{k: v for k, v in g.items() if k != "_kids"}
                                                                         for g in c.get("_kids") or []]))
                            for c in kids if c.get("_kids")]
    elif kids:
        out["_kids"] = kids
    return out
