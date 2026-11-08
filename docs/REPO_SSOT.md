# Repo as the single source of truth (Notion as an editable mirror)

```
local ──git push──▶ GitHub repo (SSOT) ──push job──▶ Notion page (properties + body)
                         ▲
                         └── pull job (every 30 min · Notion webhook · by hand) ◀── a person edits in Notion
```

- Every post is a bundle: `content/posts/<slug>/index.md` plus its images. The slug (folder name, or `slug:`
  in front matter) is the URL and never changes.
- **push** (`python -m src.ssot push`): for every bundle changed by a push, rewrite its Notion page —
  properties (Name, Slug, Date, Description, Tags, Category, isPublished = not draft, Source = hugo,
  skipRendering = on) and the whole body. Bundle images appear in Notion as `https://<site>/posts/<slug>/<file>`.
  The front matter `cover.image` becomes the page cover.
- **pull** (`python -m src.ssot pull`): for every repo page edited by a person after its last sync, render the
  body back to Markdown. Notion *file* images are downloaded into the bundle (their URLs expire in an hour).
  External images that point back at the bundle become relative paths again. Title, Description and Tags
  come back too; other front matter stays byte for byte.
  - The repo copy is untouched since the last sync: one commit on the base branch, then the deploy workflow
    starts.
  - The repo copy changed too: branch `sync/notion-<slug>-<Notion edit time>` and a PR. Nothing is
    overwritten, and main is not touched.

## How ping-pong and duplicates are prevented

| guard | where | what it stops |
|---|---|---|
| `SyncHash` property: `sha256:<bundle hash> <UTC time>` | written last by every push and pull | push skips a page whose hash already matches. A pulled edit is not pushed back. |
| last editor is a bot ⇒ skip | `human_edit_since_sync` | every engine write ends with the integration as last editor, so pull never reads our own writes |
| push never overwrites an unsynced Notion edit | push → `conflict-pending` | an edit made in Notion between two pushes waits for pull, which opens the PR |
| deterministic PR branch name + SyncHash time moved after the PR opens | `apply_pull` | the same Notion edit never opens a second PR |
| Notion page found by `notion_id` (front matter), then by `Slug`; two pages with one slug ⇒ stop | `find_page` | the same post never gets two pages |
| commit and git push first, SyncHash after | `apply_pull` | a failed git push leaves Notion "not synced", so the edit is retried and never lost |

Notion rounds `last_edited_time` down to the minute. An edit in the same minute as a sync still counts as a
change, and the content hash then decides whether there is anything to bring back.

Known limits:
- Another integration (a Notion automation, another bot) editing a page after a person hides that person's
  edit, because bot edits are skipped.
- A page whose PR is closed without merging gets the repo version on the next push of that bundle. The
  Notion edit then lives only in the closed PR's branch.
- Round trip covers paragraphs (line breaks kept), `#`–`###` headings, `-`/`1.` lists, fenced code,
  quotes, `---`, `![alt](src)` images, and `**bold** *italic* ~~strike~~ \`code\` [links](url)`.
  Deeper headings, nested lists and Markdown tables come back flattened.

## Setup

1. Notion DB: needs a `SyncHash` column of type rich_text. Run once with `--add-sync-column`. That adds
   only this column and never removes or renames any.
2. Secrets: `NOTION_TOKEN` (an integration with edit access to the DB) and `NOTION_DATABASE_ID_POSTS`.
3. Copy `examples/workflows/repo-ssot-sync.yml` and set `BASE_BRANCH`, `SSOT_SITE` and `DEPLOY_WORKFLOW`.
   Optionally set the repo variable `SSOT_ONLY=a,b` to sync only those slugs.
4. How often: the `cron:` line is the one place. `*/30 * * * *` is 30 minutes; `0 * * * *` is hourly.
5. Webhook (instant): a small relay verifies the Notion webhook signature, then calls
   `POST /repos/<owner>/<repo>/dispatches` with
   `{"event_type": "notion-changed", "client_payload": {"page_id": "<id>"}}`.
   Without `page_id`, every page is checked.
6. GitHub runs `schedule`, `repository_dispatch` and `workflow_dispatch` only from the default branch's copy of
   the workflow. On any other branch only `push` fires. A commit message containing `[ssot-pull]` runs the
   pull job there.

## For AI agents writing posts

1. `git pull` (the repo is the truth; Notion edits arrive as commits from `github-actions[bot]`).
2. Write `content/posts/<slug>/index.md` with front matter `title`, `date`, `slug`, `description`, `tags`
   and `draft`, plus images in the same folder (`![설명](cover.jpg)`, `cover.image: cover.jpg`).
3. Preview and check locally before pushing:
   - `hugo server -D`
   - Every image loads (naturalWidth > 0).
   - No broken links.
   - Every URL is https.
4. `git push`. Deploy and the Notion page update follow; nothing else to run.
5. Never rename a bundle folder or change `slug:`, because the URL and the Notion link depend on it.

When someone fixes a post in Notion in a hurry:
- Within 30 minutes (or right away through the webhook), a commit `sync(notion): <slug> <- Notion edit …`
  lands on main and deploys. Pull before your next edit.
- If you also changed that post in the meantime, a PR `sync(notion): <slug> — Notion and repo both changed`
  appears. Resolve it like any merge conflict: the branch holds the Notion version. Merging pushes the result
  back to Notion.

## Turning it off

- Revert the commit that added `.github/workflows/repo-ssot-sync.yml`:
  `git revert <sha> && git push`. Notion stays as it is, and the repo keeps every committed post.
- Old flow (Notion as source, hourly import): restore the old workflow's `schedule:` and turn the import back
  on. Pages marked `Source = hugo` / `skipRendering` stay skipped by the importer, so posts already in the repo
  are not imported twice.

## Where the code lives

`adalgu/notion-hugo-dev` is the development origin of this package. `notion-hugo-flow` is the published
copy synced from it. The engine (`src/ssot/`) was written here first (2026-11, BLOG-014). Port it back to
notion-hugo-dev before the next "Sync from dev", or that sync will drop it.
