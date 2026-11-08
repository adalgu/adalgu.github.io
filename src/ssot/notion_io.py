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
        for at in range(0, len(children), APPEND_LIMIT):
            self._call(f"blocks/{block_id}/children", "PATCH", body={"children": children[at:at + APPEND_LIMIT]})

    def replace_children(self, block_id, children, rounds=3):
        """Old body out (read to the end, delete, re-read until empty), new body in."""
        for _ in range(rounds):
            old = self.children(block_id)
            if not old:
                break
            for item in old:
                self.delete_block(item["id"])
        else:
            if self.children(block_id):
                raise RuntimeError(f"ssot: {block_id} still has old blocks after {rounds} rounds — new body not appended")
        self.append(block_id, children)
