---
name: bellosoft-github
description: "Creates Plane-compatible git branches, conventional commits, and pull requests with automatic work item linking. Use when the user says 'create branch for story [id]', 'commit', 'create PR', 'github branch', or 'github pr'."
---

# GitHub Flow

Bridges BMAD story execution with GitHub using Plane's PR state automation conventions.

**How it works:** Looks up the Plane work item for the current story, derives the ticket identifier (e.g. `NOKEY-42`), then runs git commands to create branches, commits, and PRs in the correct format so Plane auto-links and auto-transitions work item states.

**Plane PR state automation rules (from docs.plane.so/integrations/github):**

| Format in PR title | Plane behaviour |
|---|---|
| `[NOKEY-42]` — WITH brackets | Links work item + triggers **state automation** (PR merged → Done) |
| `NOKEY-42` — WITHOUT brackets | Links work item as reference only — no state automation |

**Always use brackets in PR titles** to get full automation.

**Branch naming convention:**
```
{type}/{ticket-id}-{slug}
e.g. feature/NOKEY-42-security-hardening-encryption
```

**Commit message format (Conventional Commits):**
```
{type}({ticket-id}): {description}
e.g. feat(NOKEY-42): add AES-256-GCM encryption service
```

Load `workflow.md` to begin.
