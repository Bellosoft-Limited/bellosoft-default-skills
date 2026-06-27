---
name: bellosoft-dora
description: >
  Compute DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, MTTR)
  from Jira + GitHub + Dokploy for any Bellosoft project. Triggers: "dora metrics",
  "show dora", "/bellosoft-dora AP --days 30".
---

# Skill: bellosoft-dora

**DORA (DevOps Research & Assessment) metrics** — the four key measures of software delivery performance.

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| **Deployment Frequency** | >1/day | 1/day–1/wk | 1/wk–1/mo | <1/mo |
| **Lead Time for Changes** | < 1 hour | < 1 week | < 1 month | > 1 month |
| **Change Failure Rate** | 0–15% | 0–15% | 16–30% | > 30% |
| **Mean Time to Restore** | < 1 hour | < 1 day | < 1 week | > 1 week |

---

## How Claude runs this skill

**Step 1 — Check config**

Always run `--check-config` first. It prints JSON with no prompts:

```bash
python .claude/skills/bellosoft-dora/scripts/dora_metrics.py --project AP --check-config
```

Output shape:
```json
{
  "project_configured": true,
  "project": "AP",
  "missing_credentials": {
    "dokploy": ["dokploy_url", "dokploy_token"]
  },
  "skip_flags": { "jira": false, "github": false, "dokploy": false }
}
```

**Step 2 — Fill gaps by asking the user (not the script)**

For each item in `missing_credentials`, ask the user directly in the conversation using `AskUserQuestion`. Never rely on the script's `input()` prompts — those are for terminal use only.

- `jira_url` → "What is your Jira URL? (e.g. https://yourorg.atlassian.net)"
- `jira_user` → "What is your Jira email address?"
- `jira_token` → "What is your Jira API token?" (remind user: Atlassian → Profile → Security → API tokens)
- `dokploy_url` → "What is your Dokploy URL?"
- `dokploy_token` → "What is your Dokploy API token?"

If a service is entirely missing and the user doesn't want to connect it, write the skip flag:
```bash
echo "opted-out" > .secrets/skip-dokploy.txt   # or skip-jira.txt / skip-github.txt
```

**Step 3 — Write credentials to `.secrets/`**

Write each answer as a plain text file (no quotes, trailing newline):
```bash
echo "https://yourorg.atlassian.net" > .secrets/jira-url.txt
echo "user@example.com" > .secrets/jira-username.txt
echo "ATATT3x..." > .secrets/jira-api-token.txt
echo "https://dokploy.example.com" > .secrets/dokploy-url.txt
echo "dk_..." > .secrets/dokploy-api-token.txt
```

**Step 4 — Run `--check-config` again** to confirm everything is set, then run the full script:

```bash
python .claude/skills/bellosoft-dora/scripts/dora_metrics.py --project AP --days 30
```

Use `python` not `python3` on Windows.

**Step 5 — Handle `project_configured: false`**

If the project key isn't in `docs/planning-artifacts/project-dora-config.md`, ask the user:
- Project name
- Jira board ID (integer)
- GitHub repo (e.g. Org/repo, or "none")

Then write the config file section and re-run.

---

## Project config format

`docs/planning-artifacts/project-dora-config.md`:

```markdown
## AP (AutomaPost)
- name: AutomaPost
- jira_board: 4
- github_repo: Bellosoft-Limited/AutomaPost
- dokploy_app_ids: []
- dokploy_compose_ids: [Vvs8EzlgIAv4xjHJHOWg3]
```

---

## Credential files in `.secrets/`

| File | Purpose |
|------|---------|
| `jira-url.txt` | Jira base URL |
| `jira-username.txt` | Jira email |
| `jira-api-token.txt` | Jira API token |
| `dokploy-url.txt` | Dokploy base URL |
| `dokploy-api-token.txt` | Dokploy API token |
| `skip-jira.txt` | Any content = opted out |
| `skip-github.txt` | Any content = opted out |
| `skip-dokploy.txt` | Any content = opted out |

GitHub uses `gh` CLI auth — no file needed.

---

## Data sources

- **Deployment Frequency**: Jira closed sprints + GitHub deploy workflow runs + Dokploy compose deployments
- **Lead Time**: Jira In Progress→Done changelog + PR creation→merge time
- **Change Failure Rate**: `bugs_done / total_done * 100` from Jira
- **MTTR**: Bug creation→resolution time from Jira

---

## Pitfalls

- Use `python` not `python3` on Windows
- Dokploy auth uses `x-api-key` header, not Bearer
- CFR = 0% may undercount if production bugs aren't tracked as Jira Bug type
- MTTR = 0 means no resolved bugs in period, not fast recovery
