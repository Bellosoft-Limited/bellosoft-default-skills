# Bellosoft Delivery OS — GitHub Copilot Defaults

Shared rules, agents, skills, and workflows synced into every Bellosoft client project.
Compatible with **GitHub Copilot** (VS Code).

```
bellosoft-default-skills  → company core: instructions, agents, skills, BMAD, workflows
                          → synced into any client repo via scripts/sync.ps1 or scripts/sync.sh
```

---

## Quick start — add this to your project

Run this from the root of your target project to pull in all Bellosoft defaults:

**Bash** (Linux / Mac / WSL / Git Bash):
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/scripts/sync.sh)
```

**PowerShell** (Windows):
```powershell
irm https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/scripts/sync.ps1 | iex
```

Safe to run multiple times — it overwrites everything except protected paths.

---

## Repository structure

```
bellosoft-default-skills/
├── .github/
│   ├── copilot-instructions.md    # Always-on instructions (Copilot entry point)
│   ├── instructions/              # File-based instructions (*.instructions.md)
│   ├── agents/                    # Custom agents (*.agent.md) — 6 specialists
│   ├── prompts/                   # Reusable prompt files (*.prompt.md)
│   ├── skills/                    # 50+ agent skills (BMAD, GitHub, Plane, TDD, ...)
│   ├── core/                      # Universal coding rules (loaded on-demand by agents)
│   │   ├── coding-standards.md
│   │   ├── review-checklist.md
│   │   ├── security-rules.md
│   │   ├── git-flow.md
│   │   ├── delivery-process.md
│   │   ├── github-actions.md
│   │   └── testing-patterns.md
│   ├── stack/                     # Tech-stack guidelines (loaded on-demand by agents)
│   │   ├── dotnet.md
│   │   ├── vue.md
│   │   ├── mssql.md / postgresql.md / mariadb.md
│   │   ├── azure.md
│   │   └── docker.md
│   ├── hooks/                     # Hook configurations (*.json)
│   └── workflows/                 # GitHub Actions (CI, deploy, PR validation)
├── _bmad/                         # BMAD methodology config & workflows
│   └── bmm/                       # Core module: config.yaml, orchestration, TEA
├── .vscode/                       # Editor settings (agent/prompt/hook/skill discovery)
│   └── settings.json              # chat.* locations + memory toggle
├── scripts/                       # Sync scripts (ps1 + sh)
└── README.md
```

---

## What gets synced into a client repo

The sync scripts use an **explicit allow-list** — only these folders are copied:

| Source (this repo) | Destination (client repo) | Purpose |
|---|---|---|
| `.github/` | `.github/` | Copilot instructions, agents, prompts, skills, hooks, workflows, core, stack |
| `_bmad/` | `_bmad/` | BMAD methodology config |
| `.vscode/` | `.vscode/` | VS Code settings (chat.* configs, memory toggle) |
| `scripts/` | `scripts/` | Self-updating sync scripts |

### Protected paths (never overwritten)

| Path | Belongs to |
|---|---|
| `.github/skills/bmad-tea/` | Client repo — TEA skill overrides |
| `.github/skills/reports/` | Client repo — custom reports |
| `.github/CODEOWNERS` | Client repo — team-specific ownership |

---

## Client repo structure after sync

```
client-repo/
├── .github/
│   ├── copilot-instructions.md   ← synced
│   ├── instructions/             ← synced
│   ├── agents/                   ← synced (6 specialist agents)
│   ├── core/                     ← synced (universal rules)
│   ├── stack/                    ← synced (tech-stack guidelines)
│   ├── prompts/                  ← synced
│   ├── skills/                   ← synced (50+ skills)
│   ├── hooks/                    ← synced
│   └── workflows/                ← synced (GitHub Actions)
├── .vscode/                      ← synced: settings.json with chat.* configs
├── _bmad/                        ← synced: BMAD config & workflows
└── scripts/                      ← synced: sync.ps1 + sync.sh
```

---

## Copilot configuration

| Customization | VS Code Setting | Files |
|---|---|---|
| **Always-on instructions** | `chat.instructionsFilesLocations` | `.github/instructions/*.instructions.md` |
| **Custom agents** | `chat.agentFilesLocations` | `.github/agents/*.agent.md` |
| **Prompt files** | `chat.promptFilesLocations` | `.github/prompts/*.prompt.md` |
| **Skills** | `chat.agentSkillsLocations` | `.github/skills/*/SKILL.md` |
| **Core rules** | Loaded on-demand by agents | `.github/core/*.md` |
| **Stack guidelines** | Loaded on-demand by agents | `.github/stack/*.md` |
| **MCP servers** | `mcp.json` | `.vscode/mcp.json` |
| **Hooks** | `chat.hookFilesLocations` | `.github/hooks/*.json` |
| **Memory** | `github.copilot.chat.tools.memory.enabled` | `.vscode/settings.json` |

---

## Custom Agents (`.github/agents/`)

| Agent | File | Purpose | Routes to |
|---|---|---|---|
| 🏗️ Architect | `architect.agent.md` | System architecture & technical design | BMAD skills: PRD, UX, Epics, Architecture, Research |
| 💻 Code | `code.agent.md` | Feature implementation with TDD | `bmad-dev-story` / `bmad-quick-dev` |
| 🔍 Debug | `debug.agent.md` | Issue analysis & root-cause fixing | Loads relevant core/stack guidelines |
| 📋 PM | `pm.agent.md` | Sprint planning, work items, retrospectives | `bmad-*` PM skills + `bellosoft-plane` |
| 👁️ Review | `review.agent.md` | Adversarial code review + test execution | `bmad-code-review` + `bellosoft-plane` |
| 💼 Sales | `sales.agent.md` | Proposals, estimates & client docs | Core/stack context for accurate tech descriptions |

> **Note:** `ask.agent.md` has been replaced by the built-in `@ask` participant. Use `@ask` directly for Q&A and knowledge retrieval.

---

## Skill catalog (`.github/skills/`)

| Domain | Skills | Count |
|---|---|---|
| **BMAD Core** | PRD, UX, Architecture, Epics/Stories, Implementation, Code Review, Retrospective | ~20 |
| **BMAD Testing** | TDD, ATDD, Test Design, Framework, Automation, CI, NFR, Trace, Review | ~10 |
| **BMAD Agents** | Analyst, Architect, Dev, PM, UX Designer, Tech Writer, TEA (Test Architect) | 7 |
| **BMAD Project** | Sprint Planning, Sprint Status, Correct Course, Check Readiness, Party Mode | ~10 |
| **Integrations** | `bellosoft-github` (branch/commit/PR), `bellosoft-plane` (ticket sync) | 2 |
| **Engineering** | Frontend Design, Microsoft Docs, TDD Doctrine | 3 |

---

## Key principles

1. All rules are stored in `.github/` — Copilot-native, no vendor abstraction layer
2. Use `_bmad/` methodology for multi-agent delivery workflows
3. All schema/rule files use **command-format** (actionable rules, no prose)
4. "Never Do" blocklist at the bottom of each rule file
5. `core/` and `stack/` are loaded **on-demand** by agents — not eagerly — saving context budget
6. Agents detect the project's tech stack and load only relevant guidelines