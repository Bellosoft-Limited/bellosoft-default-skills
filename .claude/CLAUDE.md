# Claude Code — Bellosoft Delivery OS

> Companion to [`copilot-instructions.md`](.github/copilot-instructions.md) for Anthropic Claude Code.

## Model Configuration

Claude Code reads project-specific models and environment variables from [`.claude/settings.json`](.claude/settings.json):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_MODEL` | Default model for all requests |
| `ANTHROPIC_SMALL_FAST_MODEL` | Quick queries, simple tasks |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Balanced tasks |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Complex reasoning |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Lightweight tasks |

Configured models:
- `bellosoft-reasoning` — default, full reasoning
- `bellosoft-complex` — Sonnet-equivalent
- `bellosoft-medium` — Opus-equivalent
- `bellosoft-simple` — fast, lightweight

## Knowledge Base

### `.agents/core/` — Universal Rules (always active)

| File | Scope |
|---|---|
| `.agents/core/coding-standards.md` | C#, TypeScript/Vue, Python naming & language rules |
| `.agents/core/review-checklist.md` | PR review with 🔴 BLOCKER · 🟡 MAJOR · 🔵 MINOR · 💡 NIT |
| `.agents/core/security-rules.md` | OWASP Top 10 + API Security Top 10 rules |
| `.agents/core/git-flow.md` | GitFlow branching: main + develop + feature/* + hotfix/* + release/* |
| `.agents/core/delivery-process.md` | Sprint lifecycle, Definition of Ready/Done |
| `.agents/core/github-actions.md` | Workflows, OIDC, permissions, secrets, branch protection |
| `.agents/core/testing-patterns.md` | TDD (Red‑Green‑Refactor), FIRST, AAA, xUnit patterns |

### `.agents/stack/` — Tech‑Specific Guidelines (context‑dependent)

| File | Stack |
|---|---|
| `.agents/stack/dotnet.md` | .NET 9/10, ASP.NET Core, EF Core conventions |
| `.agents/stack/vue.md` | Vue 3 Composition API, Nuxt 3, Pinia, TypeScript |
| `.agents/stack/mssql.md` | SQL Server 2022+, T‑SQL, indexing, performance |
| `.agents/stack/postgresql.md` | PostgreSQL 16+, PL/pgSQL, indexing, performance |
| `.agents/stack/mariadb.md` | MariaDB 11.x, MySQL 8.0, InnoDB, Galera Cluster |
| `.agents/stack/azure.md` | Azure PaaS, naming, tagging, IAM, Key Vault, networking |
| `.agents/stack/docker.md` | Multi‑stage builds, Docker Compose, security, CI |

## Custom Agents

Seven specialized agents — defined in `.claude/agents/`:

| Agent | Purpose |
|---|---|
| `architect.agent.md` | System architecture & memory bank |
| `code.agent.md` | Feature implementation & debugging |
| `debug.agent.md` | Issue analysis & root‑cause fixing |
| `ask.agent.md` | Project Q&A & knowledge retrieval |
| `pm.agent.md` | Sprint planning & work item management |
| `review.agent.md` | Adversarial code review & quality gates |
| `sales.agent.md` | Proposals, estimates & client docs |

## Prompts

Reusable prompts for recurring Claude Code workflows, located in `.agents/prompts/`:

| Prompt | Trigger |
|---|---|
| `github-branch.prompt.md` | Create GitFlow-compliant branch names |
| `github-commit.prompt.md` | Commit messages following conventional commits |
| `github-pr.prompt.md` | PR descriptions with checklist |
| `plane-sync.prompt.md` | Sync work items with Plane |
| `plane-sync-epics.prompt.md` | Epic-level Plane sync |
| `plane-sync-sprint.prompt.md` | Sprint-level Plane sync |

## Skills

Custom Claude Code skills are defined in `.claude/skills/`. Each skill lives in its own directory with a `SKILL.md` manifest.

Key skills:
- `bellosoft-github` — GitHub integration workflow
- `bellosoft-plane` — Plane project management workflow
- `banner-design` — Banner asset generation
- `bmad-*` — Full BMAD agent skill suite (analyst, architect, dev, pm, tech-writer, ux-designer)
- `bmad-advanced-elicitation` — Requirements elicitation methods

## Claude Code Directory Layout

| Customization | Claude Code Path | Purpose |
|---|---|---|
| Project instructions | `CLAUDE.md` | Always-on context |
| Memory / project docs | `.claude/CLAUDE.md` | High-level project overview |
| Settings | `.claude/settings.json` | Model config, env vars, permissions |
| Local settings | `.claude/settings.local.json` | User-specific overrides (git-ignored) |
| Custom skills | `.claude/skills/` | Reusable skill manifests |
| Prompts | `.agents/prompts/` | Reusable prompt templates |
| Agent definitions | `.claude/agents/` | BMAD agent manifests |
| Universal rules | `.agents/core/` | Always-active delivery rules |
| Tech-stack guidelines | `.agents/stack/` | Context-dependent stack rules |
| Hooks | `.claude/hooks/` | Event-driven shell commands |

## Key Principles

1. **All rules are stored in `.agents/`** — No vendor abstraction layer; both Copilot and Claude Code consume the same source of truth.
2. **Use BMAD methodology** for multi-agent delivery workflows (`bmad-*` skills and agents).
3. **All schema/rule files use command-format** — actionable rules, no prose.
4. **"Never Do" blocklist** at the bottom of each rule file.
5. **Prefer `.claude/settings.json`** for project-wide model and permission configuration.
6. **Skills are portable** — define once in `.github/skills/`, use across any Claude Code client.
7. **Keep project docs concise** — high-level overview only; detailed rules belong in `.agents/core/` and `.agents/stack/`.

## Quick Reference

### Running a BMAD Agent

```bash
# In Claude Code
cd /path/to/project
# Invoke the agent via its skill or prompt file
```
