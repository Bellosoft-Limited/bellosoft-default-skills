# Bellosoft Default Skills

Shared rules, agents, skills, and workflows synced into every Bellosoft project.
Works with **Claude Code** (primary) and **GitHub Copilot** (via `.github/`).

```
bellosoft-default-skills  → company core: instructions, agents, skills, workflows
                          → synced into any project via scripts/sync.ps1 or scripts/sync.sh
```

---

## Quick start

Run from the root of your target project:

**Bash** (Linux / Mac / WSL / Git Bash):
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/scripts/sync.sh)
```

**PowerShell** (Windows):
```powershell
irm https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/scripts/sync.ps1 | iex
```

Safe to run multiple times — it overwrites synced files but never touches protected paths.

---

## Repository structure

```
bellosoft-default-skills/
├── .claude/
│   ├── CLAUDE.md                  # Claude Code entry point — load-on-demand principles
│   ├── settings.example.json      # Example Claude Code settings
│   ├── skills/                    # Skill library (see catalog below)
│   │   └── <skill-name>/
│   │       ├── SKILL.md           # Skill instructions
│   │       └── references/        # Reference files loaded on-demand
│   └── vendor/
│       └── mattpocock-skills/     # Pinned upstream commit, LICENSE, update rules
├── .agents/
│   ├── core/                      # Universal coding rules (loaded on-demand)
│   │   ├── coding-standards.md
│   │   ├── delivery-process.md
│   │   ├── git-flow.md
│   │   ├── github-actions.md
│   │   ├── review-checklist.md
│   │   ├── security-rules.md
│   │   └── testing-patterns.md
│   ├── stack/                     # Tech-stack guidelines (loaded on-demand)
│   │   ├── dotnet.md
│   │   ├── vue.md
│   │   ├── azure.md
│   │   ├── docker.md
│   │   └── mssql.md / postgresql.md / mariadb.md
│   └── prompts/                   # Reusable prompt templates
├── .github/
│   ├── copilot-instructions.md    # GitHub Copilot entry point
│   └── agents/                    # Copilot custom agents
├── .vscode/
│   └── settings.json              # Editor settings (skill/agent discovery)
├── scripts/
│   ├── sync.sh                    # Bash sync script
│   ├── sync.ps1                   # PowerShell sync script
│   └── update-mattpocock-skills.sh  # Re-copy Matt Pocock's skills at a pinned ref
├── AGENTS.md                      # Directory map for agents (index, not instructions)
└── README.md
```

---

## What gets synced

| Source | Destination | Purpose |
|--------|-------------|---------|
| `.claude/` | `.claude/` | Claude Code skills and entry point |
| `.agents/` | `.agents/` | Core rules, stack guidelines, prompt templates |
| `.github/` | `.github/` | Copilot instructions and agents |
| `.vscode/` | `.vscode/` | Editor settings |
| `scripts/` | `scripts/` | Self-updating sync scripts |

### Seeded once (created if missing, then project-owned)

| Template | Destination | Purpose |
|----------|-------------|---------|
| `.agents/templates/docs/CODING_STANDARDS.md` | `docs/CODING_STANDARDS.md` | Standards source for `/code-review`: points to the shared `.agents/` rules and holds project-specific ones (`/retro` adds to it) |

### Protected paths (never overwritten)

| Path | Reason |
|------|--------|
| `.github/skills/bmad-tea/` | Project-specific TEA overrides |
| `.github/skills/reports/` | Project-specific report formats |
| `.github/CODEOWNERS` | Team-specific ownership |

---

## Skill catalog

Skills live in `.claude/skills/`. Load with `/skill-name` in Claude Code.

### Matt Pocock skills (vendored)

27 skills from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), copied into
`.claude/skills/` at the commit pinned in `.claude/vendor/mattpocock-skills/upstream.json`.
**Don't edit them**: updates overwrite the folders. A weekly GitHub Action opens a PR when
upstream releases; merge it when you want the update. See
[`.claude/vendor/mattpocock-skills/README.md`](.claude/vendor/mattpocock-skills/README.md).

| Skill | Purpose |
|-------|---------|
| `/setup-matt-pocock-skills` | Run once per project. Pick **Other → Jira** (see [Jira](#jira-for-matt-pocock-skills)) |
| `/grill-me`, `/grill-with-docs` | Get interviewed about a change until it's clear; `grill-with-docs` also keeps `GLOSSARY.md` and ADRs up to date |
| `/to-spec` | Turn the conversation into a spec → Jira Epic (Scrum) or a single Task (Kanban, after confirming the board) |
| `/to-tickets` | Split a spec into thin end-to-end tickets with blocking links → User Stories with dev + QA Sub-tasks (Scrum) or Tasks/Bugs (Kanban) |
| `/wayfinder` | Plan work too big for one session as a map of decision tickets |
| `/triage` | Move incoming issues through `needs-triage` → `ready-for-agent` / `ready-for-human` / `wont-do` |
| `/implement`, `/implement-spec` | Build a ticket or a whole spec, test-first, closing with a review |
| `/improve-codebase-architecture` | Find places where the code could be simplified behind smaller interfaces |
| `/ask-matt` | Not sure which skill fits? It routes you |
| `/handoff`, `/teach`, `/to-questionnaire`, `/wait-what`, `/retro` | Productivity helpers |

Model-invoked (Claude reaches for them when relevant): `tdd`, `diagnosing-bugs`, `code-review`,
`prototype`, `research`, `domain-modeling`, `codebase-design`, `pr`, `wizard`, `grilling`,
`writing-for-agents`.

> `code-review` shares its name with Claude Code's built-in `/code-review`. Type
> `/bellosoft-default-skills:code-review` (plugin install) to be sure you get Matt's.

### Delivery workflow (legacy, being retired)

`bellosoft-prd`, `bellosoft-plan-epics`, `bellosoft-plan-epic` and `bellosoft-plan-adhoc` are
being replaced by the Matt Pocock flow above. They stay available during the trial.

| Skill | Command | Purpose |
|-------|---------|---------|
| **bellosoft-prd** | `/bellosoft-prd` | Interactive requirements gathering → PRD |
| **bellosoft-audit-codebase** | `/bellosoft-audit-codebase` | Analyse existing codebase before planning → `docs/planning-artifacts/codebase-audit.md` |
| **bellosoft-plan-epics** | `/bellosoft-plan-epics` | Parse PRD → Epic register (`docs/planning-artifacts/epics.md`) |
| **bellosoft-plan-epic** | `/bellosoft-plan-epic E1` | Decompose one epic into stories + atomic tasks. Use `fix` mode to repair weak ACs in tracker |
| **bellosoft-plan-adhoc** | `/bellosoft-plan-adhoc` | Add bugs, hotfixes, or unplanned work mid-sprint |
| **bellosoft-sprint** | `/bellosoft-sprint` | Sprint overview — what's open, what's blocked, what's mine |

### Tracker integration

| Skill | Command | Purpose |
|-------|---------|---------|
| **bellosoft-jira** | `/bellosoft-jira` | Jira service layer — create epics/stories/tasks, manage sprints, transitions, imports |
| **bellosoft-sync** | `/bellosoft-sync` | Tracker sync — import, push, pull, update |

### Development

| Skill | Command | Purpose |
|-------|---------|---------|
| **bellosoft-qa-handoff** | `/bellosoft-qa-handoff` | After the PR: post what changed, how to test and the risk on the Jira ticket, for the dev's smoke test and for QA |

Legacy, not part of the new flow (kept during the trial): `bellosoft-dev-plan`, `bellosoft-dev-execute`
and `bellosoft-dev-review` (replaced by `/implement`), `bellosoft-github` (branches are created by
hand, PRs use Matt's `pr`), `bellosoft-sprint` (devs pick tickets from the board).

### Design & content

| Skill | Command | Purpose |
|-------|---------|---------|
| **design** | `/design` | Logo, icon, banner, and CIP design generation |
| **design-system** | `/design-system` | Design tokens, component specs, Tailwind integration |
| **brand** | `/brand` | Brand guidelines, color palettes, asset management |
| **frontend-design** | `/frontend-design` | Frontend UI design patterns |
| **impeccable** | `/impeccable` | UX audit, polish, accessibility, motion |
| **ui-styling** | `/ui-styling` | Tailwind + shadcn/ui styling |
| **ui-ux-pro-max** | `/ui-ux-pro-max` | Full UX/UI design workflow |
| **slides** | `/slides` | Slide deck creation |
| **ogilvy** | `/ogilvy` | Copywriting using Ogilvy principles |
| **bellosoft-document** | `/bellosoft-document` | Client-facing documents (proposals, reports, letters) on the Bellosoft template, EN or PT, as HTML, PDF or Word |
| **banner-design** | `/banner-design` | Ad banner generation |

### Engineering & content

| Skill | Command | Purpose |
|-------|---------|---------|
| **test-driven-development** | `/test-driven-development` | TDD doctrine and patterns |
| **microsoft-docs** | `/microsoft-docs` | Microsoft documentation standards |
| **seo-geo** | `/seo-geo` | SEO and GEO content optimisation |
| **reports** | `/reports` | Structured reporting templates |

---

## Planning workflow

```
/grill-with-docs                   1. Get interviewed about the change until it's clear
/to-spec                           2. Spec → Epic (Scrum) or a single Task (Kanban)
/to-tickets                        3. Tickets with blocking links → User Stories + Sub-tasks (Scrum) or Tasks (Kanban)
/implement PROJ-42                 4. Build a ticket (see Development workflow)
```

Bugs and unplanned work: `/triage`. Work too big for one session: `/wayfinder`.
No estimates are produced; tickets are sized to fit one agent session instead.

### Jira for Matt Pocock skills

Matt's skills don't support Jira themselves. They read a per-project contract from
`docs/agents/issue-tracker.md`, and ours routes every operation through `bellosoft-jira`.
Once per project:

1. `/bellosoft-jira setup` (if the project isn't connected to Jira yet)
2. `/setup-matt-pocock-skills` → Issue tracker: **Other**, "Jira via bellosoft-jira". It copies
   `.claude/skills/bellosoft-jira/references/matt-issue-tracker-jira.md` to
   `docs/agents/issue-tracker.md`. Triage labels: answer **no** to keeping the defaults and map
   `wontfix` → `wont-do`; the other four stay as they are.
3. Commit `docs/agents/`. Edit it freely: that copy belongs to the project.

Conventions the template applies (board type is detected by `/bellosoft-jira setup`):

| Board | Spec | Ticket | Children |
|---|---|---|---|
| Scrum | Epic | User Story | Development Sub-task(s) or Sub-bug(s), plus one QA Sub-task |
| Kanban | A single Task (the skill first asks whether Kanban is the right board) | Task or Bug | None (the board has a fixed QA task) |

A ticket is unblocked once every blocker is In Review, Ready for QA, Ready to Release or Done.
Won't-do work gets the `wont-do` label and moves forward like any other ticket.
Jira automation moves the development item to In Review when its PR is raised.

### Legacy planning workflow (being retired)

Produces epics, stories, and tasks from a PRD.

```
/bellosoft-prd                     1. Gather requirements → PRD
/bellosoft-audit-codebase          2. Audit existing code (if project exists)
/bellosoft-plan-epics              3. PRD → Epic register
/bellosoft-plan-epic E1            4. Decompose epic → stories + tasks
/bellosoft-plan-epic E2            5. Repeat for each epic
/bellosoft-sync push               6. Push everything to Jira
```

**Repair tasks in tracker** (missing ACs, gaps vs PRD):
```
/bellosoft-plan-epic E5 fix
```

---

## Development workflow

Jira tickets exist for tracking and to guide testing. Planning, implementation and code review
happen in the coding session.

| # | Who | How | Result |
|---|-----|-----|--------|
| 1 | Dev | Jira board, by hand | Pick a ticket and move it to **In Progress** |
| 2 | Dev | `git switch -c feature/PROJ-42-<slug>`, by hand | Working branch |
| 3 | Dev | `/implement PROJ-42` in a fresh session | Test-first build, full test run, `code-review` against our standards and the ticket, commit |
| 4 | Dev | `/pr` | Claude writes the PR body (summary, before/after evidence, risk). **Title: `#PROJ-42: <title>`**, check it before the PR is raised. Jira automation → **In Review** |
| 5 | Dev | `/bellosoft-qa-handoff` | Jira comment: what changed, how to test, risk |
| 6 | Dev | QA environment, by hand | Smoke-test by following the handoff, then move to **Ready for QA** |
| 7 | QA | QA Sub-task (Scrum) or the Task (Kanban) | Test by following the handoff → **Ready to Release** → **Done** |

- **Bugs**: a bug report in Jira starts with `/triage PROJ-42`, which turns it into a ticket ready to
  build. Then steps 2 to 7 as usual; Claude reaches for `diagnosing-bugs` on its own when the cause
  isn't obvious.
- **A whole Epic at once**: `/implement-spec PROJ-40` on a hand-made integration branch, in place of step 3.
  The PR title carries the Epic key (`#PROJ-40: <title>`), so automation doesn't move anything:
  the developer moves the Epic's items on the board by hand.
- **Backend and logic tickets with Ponytail (optional)**: the [Ponytail](https://ponytail.dev/) plugin
  keeps Claude's code to the smallest change that works. Install it once per developer with
  `/plugin marketplace add DietrichGebert/ponytail`, then `/plugin install ponytail@ponytail`. It
  doesn't change the steps above: `/implement` still builds test-first against our standards, and
  `code-review` stays the review gate. Run `/ponytail off` before a ticket with visual work (UI,
  layout, styling) and `/ponytail full` when you're back on backend work. The mode is set per repo,
  so every session open in that repo shares it.
- **Every PR still needs a human review.**

---

## Tracker detection

Skills auto-detect the active tracker from `docs/planning-artifacts/status.md`.
Credentials are stored in `.secrets/` (gitignored — never committed):

```
.secrets/
├── jira-url.txt           # or combined jira-credentials.txt
├── jira-username.txt
├── jira-api-token.txt
└── jira-identity.txt      # personal identity (account_id, email)
```

Project config (safe to commit):
```
docs/planning-artifacts/
├── status.md              # tracker preference + epic/story/task keys
├── jira-profile.md        # Jira project config (no personal data)
├── epics.md               # Epic register
├── codebase-audit.md      # Codebase audit
├── prd.md                 # Product requirements
└── epic-plans/            # Per-epic decomposition plans
    └── E{N}-plan.md
```

---

## Key principles

1. **Load on demand** — skills, core rules, and stack guidelines are loaded when needed. Nothing is eagerly pre-loaded.
2. **MCP first** — tracker operations use MCP tools (`mcp__atlassian__*`) when connected. REST fallback only when MCP is unavailable.
3. **No hardcoding** — issue type IDs, custom field IDs, and transition IDs are always discovered at runtime via the tracker API.
4. **Delegate** — `bellosoft-jira` is the only skill that calls tracker APIs directly. All others delegate to it.
5. **No personal data in docs** — credentials and identity go to `.secrets/`, never to `docs/`.
