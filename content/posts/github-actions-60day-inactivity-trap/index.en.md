---
title: "The GitHub Actions 60-Day Inactivity Trap and How I Recovered My Notion-Hugo Pipeline"
description: "Why did a blog deployment workflow running on a regular cron schedule quietly stop? An analysis of GitHub's 60-day inactivity policy (disabled_inactivity) and how I recovered."
draft: false
translationKey: "github-actions-60day-inactivity-trap"
author: Gunn Kim
cover:
  alt: Cover image for "The GitHub Actions 60-Day Inactivity Trap and How I Recovered My Notion-Hugo Pipeline"
  hiddenInList: false
  hiddenInSingle: false
  image: https://gunn.kim/covers/github-actions-60day.jpg
date: '2026-09-06'
keywords: &id001
- GitHub Actions
- Hugo
- Notion
- Automation
- CI/CD
lastmod: '2026-11-08T15:46:00.000Z'
notion_id: 3d37522e-eb2f-81fa-aa32-e5b8aed5c366
slug: "github-actions-60day-inactivity-trap"
tags: *id001
---
## 1. How It Started: I Wrote a Post in Notion, So Why Isn't It Deploying?

My personal tech blog ([gunn.kim](https://gunn.kim)) runs on a fully automated pipeline: **Notion serves as a headless CMS, and every hour on the hour (`0 * * * *`) GitHub Actions reads the posts from a Notion database, builds them with Hugo (PaperMod), and deploys them to GitHub Pages**.

Recently, though, I wrote a new post and switched on `isPublished: true`, and hours later it still hadn't shown up on the website.

I hadn't run a manual build locally, and the Notion API key hadn't expired either. So what was the problem?

---

## 2. Diagnosis: The Silent Killer, `disabled_inactivity`

I traced the workflow's status through the Actions tab of the GitHub repository and the GitHub CLI (`gh`).

```bash
gh workflow list --repo adalgu/adalgu.github.io
```

The output was a shock:

```plain text
Notion → Hugo → GitHub Pages  disabled_inactivity  5293739
```

The status wasn't `active`. It was locked in **`disabled_inactivity`**!

### GitHub Actions' Hidden Policy

According to GitHub's official documentation:

> **In a public or private repository with no commits or activity for 60 days, scheduled workflows (`schedule` cron) are automatically disabled to avoid wasting cost and compute resources.**

The last commit was sometime around May 2026, and in the 60 days after that the repository itself saw no Git commits at all.

No matter how many posts I wrote or edited in Notion, none of that counts as a Git commit inside the GitHub repository, so GitHub's system judged this repo to be an **"abandoned, idle repository"** and shut off the scheduler.

---

## 3. The Fix: Immediate Recovery and a Manual Trigger

Once I knew the cause, the fix was clear. Using the GitHub CLI, I turned the workflow back on right away and triggered it manually.

```bash
# 1. 비활성화된 워크플로우 재활성화
gh workflow enable notion-hugo-deploy.yml --repo adalgu/adalgu.github.io

# 2. 즉시 빌드 트리거
gh workflow run notion-hugo-deploy.yml --repo adalgu/adalgu.github.io
```

About 1 minute and 27 seconds later, GitHub Actions had called the Notion API to fetch the latest posts, finished the Hugo build successfully, and deployed to GitHub Pages without a hitch (HTTP 200).

```markdown
graph TD
    A[Notion Database: Blog Posts] -->|1. isPublished: true| B(GitHub Actions Runner)
    B -->|2. notion_hugo_app.py| C[Markdown Files in content/posts]
    C -->|3. hugo --minify| D[Public HTML Assets]
    D -->|4. deploy-pages| E[GitHub Pages: adalgu.github.io]
    E -->|5. Cloudflare CDN CNAME| F[Final: https://gunn.kim]
```

---

## 4. Structural Improvements: What Did I Learn?

Here are the three key lessons I took away from this troubleshooting session:

1. **The asymmetry between an external CMS and a Git scheduler**:

- If you only update data externally (in Notion), the repository looks idle from GitHub's point of view, and the scheduler gets locked.
- So you need to either **make Git commits the single source of truth (SSOT) for your posts** or run a workflow alongside it that pings the repo with a regular keep-alive commit.
2. **Building a one-click deploy CLI**:

- Rather than just waiting out the hourly cycle, I built `gunn-publish`, a global command on my local machine that pushes changes live straight from the terminal:
```bash
     gunn-publish
```

3. **The need for autonomous monitoring**:

- When the pipeline stops, a person shouldn't be the one who notices after the fact. A monitoring layer is essential, where an agent or cron workflow periodically watches for the `disabled_inactivity` status and sends an alert.
Automation isn't finished just because you've built it once. It's only complete when you keep monitoring for the platform provider's policy changes and for silent failures.
