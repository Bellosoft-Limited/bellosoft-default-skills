# Agents and Skills Catalog

Index only — load on demand, never pre-load.

## Directory Map

| Resource | Path |
|---|---|
| Core instructions | `.claude/CLAUDE.md` |
| Skills | `.claude/skills/<name>/SKILL.md` |
| Agents | `.claude/agents/*.agent.md` |
| Stack guidelines | `.agents/stack/<name>.md` |
| Universal rules | `.agents/core/<name>.md` |
| Prompt templates | `.agents/prompts/<name>.prompt.md` |
| Tracker bootstrap | `.claude/skills/bellosoft-jira/references/tracker-bootstrap.md` |
| Matt Pocock skills (vendored, don't edit) | `.claude/vendor/mattpocock-skills/README.md` |

## Discovery

```bash
skill                        # list all skills
ls .claude/agents/           # list agents
ls .agents/stack/            # list stack rules
ls .agents/core/             # list core rules
ls .agents/prompts/          # list prompt templates
```

## Agent skills

Used by the Matt Pocock skills (`/to-spec`, `/to-tickets`, `/triage`, `/wayfinder`, ...). Per-project details live in `docs/agents/`; if it's missing, run `/setup-matt-pocock-skills`.

### Issue tracker

Jira, through the `bellosoft-jira` skill. See `docs/agents/issue-tracker.md`; when setting it up, copy it from `.claude/skills/bellosoft-jira/references/matt-issue-tracker-jira.md`.

### Triage labels

`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wont-do` for the `wontfix` role. See `docs/agents/triage-labels.md`.

### Branches and pull requests

The developer creates the working branch by hand; skills work on the current branch. PR title: `#<KEY>: <title>`, where KEY is the development item (Sub-task/Sub-bug on Scrum, Task/Bug on Kanban), or the Epic for a whole-Epic PR from `/implement-spec`. PR body: the `pr` skill. Details in `docs/agents/issue-tracker.md` → "How work is closed".

### Domain docs

Single-context unless `GLOSSARY-MAP.md` exists. See `docs/agents/domain.md`.
