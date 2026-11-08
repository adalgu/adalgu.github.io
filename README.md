# Notion-Hugo

> Transform your Notion workspace into a blazing-fast Hugo blog with smart automation.

[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Hugo](https://img.shields.io/badge/Hugo-Extended-FF4088?logo=hugo&logoColor=white)](https://gohugo.io)
[![Notion API](https://img.shields.io/badge/Notion-API%20v2-000000?logo=notion&logoColor=white)](https://developers.notion.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)

## Writing posts (repo is the source of truth) — for AI agents and people

This repo is the one source of every post. Notion is an editable mirror (BRIEF-BL-005, BLOG-014/017).
Full guide: [docs/REPO_SSOT.md](docs/REPO_SSOT.md).

1. `git pull`. Notion edits arrive as commits from `github-actions[bot]`.
2. Write `content/posts/<slug>/index.md` (front matter `title`, `date`, `slug`, `description`, `tags`,
   `draft`) and put its images in the same folder.
3. Run `make check` (or `npm run check`): pull, hugo build, static server, browser check. It checks that every
   image has naturalWidth > 0, there is no `http://` href or src, there are no internal 4xx and the icons
   return 200. It prints JSON and an exit code.
4. `git push`. These follow by themselves:
   - deploy (`notion-hugo-deploy.yml`);
   - the live-site browser check (`site-check` job);
   - the Notion page update (`repo-ssot-sync.yml`).

Never rename a bundle or change `slug:`; that is the URL. Two published pages at one URL stop the build
(`scripts/check_duplicate_urls.py`).

**Urgent fix in Notion**:
- Within 30 minutes (or right away through the webhook), a commit `sync(notion): <slug> <- Notion edit …`
  lands and deploys. The page cover comes back too.
- If the repo copy also changed, a PR `sync(notion): <slug> — Notion and repo both changed` opens instead.
  Until it is merged, pushes leave that Notion page alone. Merge it like any PR; the merge pushes the result
  back to Notion.

### First run on main (after the merge card) — in this order

1. The Notion DB has the `SyncHash` column (rich_text; added 2026-11-09, BLOG-014). The repo secrets
   `NOTION_TOKEN` and `NOTION_DATABASE_ID_POSTS` are already set. Repo variable `SSOT_ONLY` stays empty.
2. **Dry run first**: Actions → Repo SSOT sync → Run workflow on `main`, direction `push`, `dry_run` on. The log
   lists `write`, `create` or `same` for every bundle. Moved posts are found by their `notion_id`, so none
   should say `create`.
3. The merge push itself runs `push-to-notion` for every bundle the merge touched. For each one it:
   1. sets Source = hugo, skipRendering = on and the other properties;
   2. replaces the body;
   3. writes SyncHash **last**.

   The job stops at the first error and the remaining pages are untouched. Rerunning (step 2 without
   `dry_run`) resumes: pages already written match their hash and say `same`.
4. Pull starts on the next 30-minute tick. Pages never written by push have no SyncHash and are skipped
   (`never synced`).

### Turn it off / go back

- **Stop syncing only**: `git revert <commit that added .github/workflows/repo-ssot-sync.yml> && git push`.
- **Back to the old flow** (Notion as the source):
  1. `git revert -m 1 <merge commit of this PR> && git push`. This restores the hourly import, its cache and
     the mirror job, and removes the moved bundles.
  2. `python scripts/release_notion_pages.py --apply` (dry run without `--apply`). This sets Source = notion and
     skipRendering = off on the moved posts' pages, so the old import takes them again.

## Why Notion-Hugo?

**Write in Notion. Publish with Hugo. Deploy anywhere.**

After 15+ years building content systems at scale, I've learned that the best tools get out of your way. Notion-Hugo bridges the gap between Notion's intuitive editing experience and Hugo's unmatched static site performance.

### Key Features

- 🚀 **Smart Sync** - Incremental updates, only syncs what changed
- 🎯 **Zero Config** - Auto-detects environment, configures accordingly  
- 📦 **GitHub Pages First** - Optimized for GitHub's free hosting
- 🔄 **CI/CD Ready** - GitHub Actions workflow included
- 🎨 **Theme Included** - PaperMod pre-configured and optimized
- 🔍 **SEO Optimized** - Structured data, meta tags, sitemaps

## Quick Start

```bash
# One command setup
git clone https://github.com/adalgu/adalgu.github.io.git
cd adalgu.github.io
python app.py quickstart --token YOUR_NOTION_TOKEN
```

That's it. Your blog is ready. Push to GitHub and it's live in 5 minutes.

## How It Works

```mermaid
graph LR
    A[Write in Notion] --> B[Check 'Publish' Box]
    B --> C[GitHub Action Triggers]
    C --> D[Sync & Build]
    D --> E[Deploy to GitHub Pages]
    E --> F[Live Blog]
```

## Installation

### Prerequisites

- Python 3.8+
- Git
- Notion API key ([Get one here](https://www.notion.so/my-integrations))

### Method 1: Automated Setup (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/adalgu/adalgu.github.io/main/scripts/quickstart-github.sh | bash
```

### Method 2: Manual Setup

```bash
# 1. Clone
git clone https://github.com/adalgu/adalgu.github.io.git
cd adalgu.github.io

# 2. Install dependencies
pip install -r dev/requirements.txt

# 3. Run quickstart
python app.py quickstart --token YOUR_NOTION_TOKEN

# 4. Add GitHub Secret
# Go to: Settings → Secrets → Actions
# Add: NOTION_TOKEN = your_token

# 5. Push
git push origin main
```

## Configuration

### Smart Defaults

Notion-Hugo automatically detects and configures:

- **Base URL** - GitHub Pages URL structure
- **Theme** - PaperMod with optimal settings
- **Deployment** - GitHub Actions workflow
- **Caching** - Smart incremental sync

### Environment Variables

```bash
# Required
NOTION_TOKEN=your_notion_integration_token

# Optional
HUGO_BASE_URL=https://custom.domain.com  # Override auto-detection
GA_ID=G-XXXXXXXXXX                       # Google Analytics
```

### Notion Properties → Hugo Frontmatter

| Notion Property | Hugo Frontmatter | Type | Required |
|---|---|---|---|
| Name | title | text | ✅ |
| Date | date | date | ✅ |
| isPublished | draft | checkbox | ✅ |
| Description | description | text | |
| Tags | tags | multi-select | |
| Categories | categories | multi-select | |
| Featured | featured | checkbox | |

## Usage

### Daily Workflow

```bash
# Sync content from Notion
python app.py sync

# Build and preview locally
python app.py build --serve

# Validate setup
python app.py validate --fix
```

### CLI Commands

| Command | Description |
|---|---|
| `quickstart` | Complete setup with smart configuration |
| `sync` | Sync content from Notion to Hugo |
| `build` | Build Hugo static site |
| `validate` | Check configuration |
| `status` | Show system status |

### Advanced Options

```bash
# Full sync (rebuild everything)
python app.py sync --full

# Dry run (preview changes)
python app.py sync --dry-run

# GitHub Pages validation
python app.py validate --github

# Deploy to Vercel (optional)
python app.py quickstart --deploy-target both
```

## Architecture

### Project Structure

```
notion-hugo/
├── app.py              # CLI entry point
├── src/
│   ├── smart_config.py # Auto-configuration
│   ├── notion_hugo.py  # Core sync engine
│   └── ...
├── content/            # Hugo content (auto-generated)
├── themes/PaperMod/    # Included theme
└── .github/workflows/  # CI/CD pipeline
```

### Performance

- **Incremental Sync** - Only processes changed pages
- **Parallel Processing** - Batch operations for speed
- **Smart Caching** - State tracking reduces API calls
- **CDN Ready** - Static assets optimized for edge delivery

## Deployment Options

### GitHub Pages (Primary)

Automatic deployment via GitHub Actions. Zero configuration required.

```yaml
# .github/workflows/notion-hugo-deploy.yml
name: Notion → Hugo → GitHub Pages
on:
  push: [main]
  schedule: [{cron: '0 */2 * * *'}]  # Every 2 hours
```

### Vercel (Optional)

For preview deployments and custom domains:

```bash
python app.py quickstart --deploy-target vercel
vercel --prod
```

### Self-Hosted

```bash
# Build locally
python app.py sync && hugo

# Serve static files
cd public && python -m http.server 8000
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|---|---|
| Notion API timeout | Check token permissions |
| Hugo build fails | Run `python app.py validate --fix` |
| GitHub Pages 404 | Wait 5-10 minutes for DNS |
| Sync not working | Check `isPublished` property |

### Debug Mode

```bash
# Verbose logging
export DEBUG=1
python app.py sync

# Check state file
cat .notion-hugo-state.json
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

```bash
# Install dev dependencies
pip install -r dev/requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/
```

## Performance Metrics

Based on production deployments:

- **Sync Time**: ~2s for 10 posts (incremental)
- **Build Time**: <5s for 100 posts
- **Deploy Time**: <60s total (GitHub Actions)
- **Page Speed**: 100/100 Lighthouse score

## Security

- Notion token stored as GitHub Secret
- No sensitive data in repository
- Static output (no server vulnerabilities)
- Automated dependency updates

## Roadmap

- [ ] Multi-language support
- [ ] Custom shortcodes
- [ ] Image optimization pipeline
- [ ] Notion databases → Hugo data files
- [ ] Comment system integration

## License

GPL-3.0 License - see [LICENSE](LICENSE)

## Acknowledgments

Built on the shoulders of giants:

- [Hugo](https://gohugo.io) - The world's fastest static site generator
- [Notion API](https://developers.notion.com) - Powerful content API
- [PaperMod](https://github.com/adityatelange/hugo-PaperMod) - Clean, elegant theme

## Author

**Gunn Kim** - Applied Scientist with 15+ years in production systems

- GitHub: [@adalgu](https://github.com/adalgu)
- Blog: [gunn.kim](https://gunn.kim)

---

<p align="center">
  <strong>If this project helps you, consider giving it a ⭐</strong><br>
  <em>Transform your Notion into a blog in 5 minutes</em>
</p>
