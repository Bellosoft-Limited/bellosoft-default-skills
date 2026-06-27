---
name: bellosoft-dora
description: >
  Compute DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, MTTR)
  from Jira + GitHub + Dokploy for any Bellosoft project. Triggers: "dora metrics",
  "show dora", "/bellosoft-dora AP --days 30".
---

# Skill: bellosoft-dora

**DORA (DevOps Research & Assessment) metrics** — the four key measures of software delivery performance identified by Forsgren, Humble & Kim (2018).

| Metric | What it measures | Elite | High | Medium | Low |
|--------|-----------------|-------|------|--------|-----|
| **Deployment Frequency** | How often code ships to production | On demand (multiple/d) | Between 1/d and 1/wk | Between 1/wk and 1/mo | Less than 1/mo |
| **Lead Time for Changes** | Time from commit to production | < 1 hour | < 1 week | < 1 month | > 1 month |
| **Change Failure Rate** | % of deploys causing failures | 0–15% | 0–15% | 16–30% | > 30% |
| **Mean Time to Restore** | Time to recover from failure | < 1 hour | < 1 day | < 1 week | > 1 week |

> ⚠️ In the 2021+ DORA reports, Elite and High bands were merged for CFR — both are 0–15%.

---

## Quick Start

```
/bellosoft-dora                         # AP project, last 30 days
/bellosoft-dora AP --days 90            # AutomaPost, 90 days
/bellosoft-dora AU --days 30            # 123auto, 30 days
```

The skill auto-discovers board IDs, repo names, and Dokploy project mappings.

---

## Credential Setup

Run setup once:

```
/bellosoft-dora setup
```

**Required (saved to `.secrets/`):**
- Jira: `jira-url.txt`, `jira-username.txt`, `jira-api-token.txt`
- GitHub: uses `gh` CLI auth
- Dokploy (optional): `dokploy-url.txt`, `dokploy-api-token.txt`

If missing, the skill prompts for them.

---

## Project Configuration

Projects are mapped in `.claude/skills/bellosoft-dora/references/projects.yaml` or in `docs/planning-artifacts/project-dora-config.md`.

Default mappings:

| Project | Key | Jira Board | GitHub Repo | Dokploy Apps |
|---------|-----|------------|-------------|--------------|
| AutomaPost | AP | 4 | Bellosoft-Limited/AutomaPost | — |
| 123auto | AU | 5 | Bellosoft-Limited/123auto | — |
| AutomaLead | AUT | 8 | Bellosoft-Limited/automaLead | — |

To configure Dokploy app IDs for a project, add to `docs/planning-artifacts/project-dora-config.md`:
```markdown
## AP (AutomaPost)
- jira_board: 4
- github_repo: Bellosoft-Limited/AutomaPost
- dokploy_app_ids: [automa-post, automa-post-api]
```

---

## Data Sources & Collection

### 1. Deployment Frequency

Collect from 3 sources (in priority order):
- **GitHub Actions**: query `repos/{repo}/actions/runs?status=success`, filter workflows with "deploy" or "release"
- **Dokploy**: `POST /api/deployment.all?applicationId={id}` with `Authorization: api-key *** header
- **Jira Sprints**: `GET /rest/agile/1.0/board/{id}/sprint`, count closed sprints in period

### 2. Lead Time for Changes

Two proxies:
- **Jira cycle time**: fetch changelogs for Done issues, measure In Progress → Done transition
- **PR cycle time**: from `gh api repos/{repo}/pulls`, measure time from PR creation → merge

### 3. Change Failure Rate

Count bugs completed vs total completed issues on the Jira board:
```
CFR = bugs_done / total_done * 100
```

### 4. Mean Time to Restore (MTTR)

Measure time from bug creation → resolution for completed bugs in Jira.

---

## Execution

The preferred way to compute metrics is via the collector script:

```bash
python3 scripts/dora_metrics.py --project AP --days 30
```

If the script is unavailable, execute the collection steps manually using `curl` and `gh` CLI queries as described in the references section.

The script:
1. Checks all credential files
2. Fetches from each data source (gracefully skips unavailable ones)
3. Computes metrics and classifies into DORA bands
4. Outputs a formatted table with recommendations
5. Saves detailed report to `docs/dora/dora-report-{project}-{date}.md`

---

## Output Format

```text
╔══════════════════════════════════════════════════════════════════════════╗
║  📊 DORA METRICS — AP (AutomaPost)  •  2026-05-28 → 2026-06-27  (30d)  ║
╚══════════════════════════════════════════════════════════════════════════╝

  Metric                          Value        DORA Band
  1. Deployment Frequency    0.2/wk       🥈 Medium
     Sources: 1 sprints + 0 GH deploys + 0 Dokploy
  2. Lead Time (Jira cycle)  1.3d         🥇 High
  3. Change Failure Rate     0.0%         🏆🥇 Elite/High
  4. Mean Time to Restore    0m           🏆 Elite

  DATA SOURCES & RAW COUNTS
  🐙 GitHub:  44 commits, 4 PRs merged
  🚀 Dokploy: 0 deployments
  📋 Jira:    154 total, 23 completed, 5 open bugs
```

---

## Pitfalls

- **Jira REST `/rest/api/3/search`** may return 410 Gone — use Agile API `/rest/agile/1.0/board/{id}/issue` instead
- **Dokploy auth**: `Authorization: api-key {token}`, NOT Bearer token
- **CFR = 0%** is misleading if production bugs aren't tracked as Jira Bug issues
- **MTTR = 0** means no resolved bugs in period, not fast recovery
- **Jira board ID changes** — update `project-dora-config.md` if a new board is created
- **GitHub rate limits** — 5000 req/hr; if exceeded use commit-count-only mode
- **Dokploy API** returns all deployments — filter client-side by date

---

## References

- `references/dora-bands.md` — Full DORA performance band definitions
- `scripts/dora_metrics.py` — The collector script for automated execution
