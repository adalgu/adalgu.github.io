"""Repo-as-SSOT sync engine: the git repository is the only source of posts; Notion is an editable mirror.

    push  repo -> Notion   a bundle (content/posts/<slug>/) changed in a commit -> its Notion page is rewritten,
                           properties and body, unless the content hash already matches the page's SyncHash.
    pull  Notion -> repo   a page edited by a person (not a bot) after its last sync -> Markdown back into the
                           bundle. Repo untouched since that sync = commit on the base branch; repo also changed =
                           sync/notion-<slug>-<time> branch + PR (nothing overwritten).

Ping-pong guard: every engine write leaves a bot as the page's last editor (pull skips bot edits), and the
SyncHash property holds the bundle hash both sides agreed on (push skips equal hashes).
See docs/REPO_SSOT.md.
"""
