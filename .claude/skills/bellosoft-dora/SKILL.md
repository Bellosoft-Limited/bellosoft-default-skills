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
/bellosoft-dora AP --days 30    # AutomaPost, last 30 days
/bellosoft-dora AU --days 90    # 123auto, 90 days
/bellosoft-dora --setup         # One-time credential + project setup
```

---

## Credential & Project Setup

Run setup once before first use:

```
python3 scripts/dora_metrics.py --setup
```

Setup will ask whether to connect each service. Saying **no** records an opt-out so
it won't ask again. Saying **yes** prompts for credentials.

**Credentials saved to `.secrets/`:**
- Jira: `jira-url.txt`, `jira-username.txt`, `jira-api-token.txt`
- GitHub: uses `gh` CLI auth (run `gh auth login` separately)
- Dokploy: `dokploy-url.txt`, `dokploy-api-token.txt`

**Opt-out flags (written when user skips a service):**
- `.secrets/skip-jira.txt`
- `.secrets/skip-github.txt`
- `.secrets/skip-dokploy.txt`

Delete the relevant skip file to re-enable a service.

---

## Project Configuration

Projects are stored in `docs/planning-artifacts/project-dora-config.md`.
**There are no hardcoded defaults** — if a project key is not in that file, setup runs automatically.

Example config file:
```markdown
## AP (AutomaPost)
- name: AutomaPost
- jira_board: 4
- github_repo: Bellosoft-Limited/AutomaPost
- dokploy_app_ids: []
- dokploy_compose_ids: [Vvs8EzlgIAv4xjHJHOWg3]

## AU (123auto)
- name: 123auto
- jira_board: 5
- github_repo: Bellosoft-Limited/123auto
- dokploy_app_ids: []
- dokploy_compose_ids: []
```

When Dokploy credentials exist but no compose IDs are configured, the script
auto-discovers them by querying Dokploy for projects matching the project key.

---

## Data Sources & Collection

### 1. Deployment Frequency

Collected from 3 sources:
- **Jira Sprints**: closed sprints in period (`/rest/agile/1.0/board/{id}/sprint`)
- **GitHub Actions**: deploy/release workflow runs (`repos/{repo}/actions/runs`)
- **Dokploy**: compose deployments (`/api/deployment.allByCompose?composeId={id}`)

### 2. Lead Time for Changes

Two proxies:
- **Jira cycle time**: In Progress → Done transition (via changelog API)
- **PR cycle time**: PR creation → merge (`gh api repos/{repo}/pulls`)

### 3. Change Failure Rate

```
CFR = bugs_done / total_done * 100
```

### 4. Mean Time to Restore (MTTR)

Bug creation → resolution for completed Jira Bugs.

---

## Execution

```bash
python3 .claude/skills/bellosoft-dora/scripts/dora_metrics.py --project AP --days 30
```

The script:
1. Reads credentials and skip flags from `.secrets/`
2. Loads project config from `docs/planning-artifacts/project-dora-config.md`
3. If project missing → runs project setup interactively
4. If credentials missing for a non-skipped service → offers to run setup
5. Fetches from each data source (gracefully skips opted-out/unconfigured ones)
6. Computes metrics and classifies into DORA bands
7. Prints formatted report and saves to `docs/dora/dora-report-{project}-{date}.md`

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
```

---

## Pitfalls

- **Jira REST `/rest/api/3/search`** may return 410 Gone — use Agile API instead
- **Dokploy auth**: `x-api-key: {token}` header, NOT Bearer
- **CFR = 0%** is misleading if production bugs aren't tracked as Jira Bug issues
- **MTTR = 0** means no resolved bugs in period, not fast recovery
- **GitHub rate limits** — 5000 req/hr; if exceeded, commit-count-only mode

---

## References

- `references/dora-bands.md` — Full DORA performance band definitions
- `scripts/dora_metrics.py` — The collector script
