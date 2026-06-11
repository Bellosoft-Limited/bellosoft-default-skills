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
│   └── skills/                    # Skill library (see catalog below)
│       └── <skill-name>/
│           ├── SKILL.md           # Skill instructions
│           └── references/        # Reference files loaded on-demand
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
│   └── sync.ps1                   # PowerShell sync script
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

### Protected paths (never overwritten)

| Path | Reason |
|------|--------|
| `.github/skills/bmad-tea/` | Project-specific TEA overrides |
| `.github/skills/reports/` | Project-specific report formats |
| `.github/CODEOWNERS` | Team-specific ownership |

---

## Skill catalog

Skills live in `.claude/skills/`. Load with `/skill-name` in Claude Code.

### Delivery workflow

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
| **bellosoft-plane** | `/bellosoft-plane` | Plane.so service layer — same operations for Plane |
| **bellosoft-sync** | `/bellosoft-sync` | Tracker sync — import, push, migrate (Plane→Jira or Jira→Plane), replan-and-migrate |

### Development workflow

| Skill | Command | Purpose |
|-------|---------|---------|
| **bellosoft-dev-plan** | `/bellosoft-dev-plan PROJ-42` | TDD-based implementation plan for a story |
| **bellosoft-dev-execute** | `/bellosoft-dev-execute` | Execute the plan: RED → GREEN → REFACTOR cycle |
| **bellosoft-dev-review** | `/bellosoft-dev-review` | Code review + test coverage check before PR |
| **bellosoft-github** | `/bellosoft-github branch` | Branch naming, conventional commits, PR creation |

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

The delivery workflow picks up after a PRD exists and produces properly structured
epics, stories, and tasks in your tracker of choice.

```
/bellosoft-prd                     1. Gather requirements → PRD
/bellosoft-audit-codebase          2. Audit existing code (if project exists)
/bellosoft-plan-epics              3. PRD → Epic register
/bellosoft-plan-epic E1            4. Decompose epic → stories + tasks
/bellosoft-plan-epic E2            5. Repeat for each epic
/bellosoft-sync push               6. Push everything to Jira or Plane
```

**Tracker migration** (e.g. Plane → Jira with replanning):
```
/bellosoft-sync replan-and-migrate
```
Imports from source → runs plan-epics → decomposes each epic → migrates to destination.

**Repair tasks in tracker** (missing ACs, gaps vs PRD):
```
/bellosoft-plan-epic E5 fix
```

---

## Development workflow

```
/bellosoft-sprint                  See what's in the sprint
/bellosoft-dev-plan PROJ-42        Plan the story (TDD approach)
/bellosoft-github branch           Create feature branch
/bellosoft-dev-execute             Implement: RED → GREEN → REFACTOR
/bellosoft-dev-review              Review before PR
/bellosoft-github commit           Conventional commit
/bellosoft-github pr               Open PR
```

---

## Tracker detection

Skills auto-detect the active tracker from `docs/planning-artifacts/status.md`.
Credentials are stored in `.secrets/` (gitignored — never committed):

```
.secrets/
├── jira-url.txt           # or combined jira-credentials.txt
├── jira-username.txt
├── jira-api-token.txt
├── jira-identity.txt      # personal identity (account_id, email)
└── plane-api-key.txt
```

Project config (safe to commit):
```
docs/planning-artifacts/
├── status.md              # tracker preference + epic/story/task keys
├── jira-profile.md        # Jira project config (no personal data)
├── plane-profile.md       # Plane project config
├── epics.md               # Epic register
├── codebase-audit.md      # Codebase audit
├── prd.md                 # Product requirements
└── epic-plans/            # Per-epic decomposition plans
    └── E{N}-plan.md
```

---

## Key principles

1. **Load on demand** — skills, core rules, and stack guidelines are loaded when needed. Nothing is eagerly pre-loaded.
2. **MCP first** — tracker operations use MCP tools (`mcp__atlassian__*`, `mcp_plane_*`) when connected. REST fallback only when MCP is unavailable.
3. **No hardcoding** — issue type IDs, custom field IDs, and transition IDs are always discovered at runtime via the tracker API.
4. **Delegate** — `bellosoft-jira` and `bellosoft-plane` are the only skills that call tracker APIs directly. All others delegate to them.
5. **No personal data in docs** — credentials and identity go to `.secrets/`, never to `docs/`.
