# Claude Code — Project Instructions

This file is always loaded. Keep it minimal — details live in `AGENTS.md`.

## Core Principles

- **Load on demand** — never pre-load rules; fetch only what the current task needs
- **Delegate complex work** — use `task` for multi-step agents, `skill` for domain rules
- **Lean context** — summarise completed sections to keep the context window clean

## How to Work

1. Check `AGENTS.md` for the directory map and what is available
2. Load what you need — skill manifests via `skill`, plain files via `read`
3. Delegate complex or parallel work via `task`

## Loading Rules

**Skills** — load via `skill` tool (run `skill` with no args to list all):
```
skill name="bellosoft-plan-epic"
```

**Stack, core, and prompt files** — read directly:
```
read .agents/stack/dotnet.md
read .agents/core/security-rules.md
```

**Agents** — delegate via `task`:
```
task subagent_type="code" prompt="Implement user login"
```

## Reference

See `AGENTS.md` for the full directory map and discovery commands.

## Agent skills

Used by the Matt Pocock skills (`/to-spec`, `/to-tickets`, `/triage`, `/wayfinder`, ...). Per-project details live in `docs/agents/`; if it's missing, run `/setup-matt-pocock-skills`.

### Issue tracker

Jira, through the `bellosoft-jira` skill. See `docs/agents/issue-tracker.md`; when setting it up, copy it from `.claude/skills/bellosoft-jira/references/matt-issue-tracker-jira.md`.

### Triage labels

`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wont-do` for the `wontfix` role. See `docs/agents/triage-labels.md`.

### Branches and pull requests

The developer might have created the working branch by hand, which can be identified if the current branch is not 'develop' nor 'master'; skills work on the current branch. PR title: `#<KEY>: <title>`, where KEY is the development item (Sub-task/Sub-bug on Scrum, Task/Bug on Kanban), or the Epic for a whole-Epic PR from `/implement-spec`. PR body: the `pr` skill. Details in `docs/agents/issue-tracker.md` → "How work is closed".

### Domain docs

Single-context unless `GLOSSARY-MAP.md` exists. See `docs/agents/domain.md`.
