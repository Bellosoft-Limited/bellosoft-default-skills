# Copilot Instructions — Bellosoft Delivery OS

## Knowledge Base

### `core/` — Universal Rules (always active)
- `.agents/core/coding-standards.md` — C#, TypeScript/Vue, Python naming & language rules
- `.agents/core/review-checklist.md` — PR review with 🔴 BLOCKER · 🟡 MAJOR · 🔵 MINOR · 💡 NIT
- `.agents/core/security-rules.md` — OWASP Top 10 + API Security Top 10 rules
- `.agents/core/git-flow.md` — GitFlow branching: main + develop + feature/* + hotfix/* + release/*
- `.agents/core/delivery-process.md` — Sprint lifecycle, Definition of Ready/Done
- `.agents/core/github-actions.md` — Workflows, OIDC, permissions, secrets, branch protection
- `.agents/core/testing-patterns.md` — TDD (Red‑Green‑Refactor), FIRST, AAA, xUnit patterns


### `stack/` — Tech‑Specific Guidelines (context‑dependent)
- `.agents/stack/dotnet.md` — .NET 9/10, ASP.NET Core, EF Core conventions
- `.agents/stack/vue.md` — Vue 3 Composition API, Nuxt 3, Pinia, TypeScript
- `.agents/stack/mssql.md` — SQL Server 2022+, T‑SQL, indexing, performance
- `.agents/stack/postgresql.md` — PostgreSQL 16+, PL/pgSQL, indexing, performance
- `.agents/stack/mariadb.md` — MariaDB 11.x, MySQL 8.0, InnoDB, Galera Cluster
- `.agents/stack/azure.md` — Azure PaaS, naming, tagging, IAM, Key Vault, networking
- `.agents/stack/docker.md` — Multi‑stage builds, Docker Compose, security, CI

## Custom Agents

Seven specialized agents — defined in `.claude/agents/` 
- `architect.agent.md` — System architecture & memory bank
- `code.agent.md` — Feature implementation & debugging
- `debug.agent.md` — Issue analysis & root‑cause fixing
- `ask.agent.md` — Project Q&A & knowledge retrieval
- `pm.agent.md` — Sprint planning & work item management
- `review.agent.md` — Adversarial code review & quality gates
- `sales.agent.md` — Proposals, estimates & client docs

## Copilot Configuration

| Customization | Copilot (VS Code) |
|---|---|
| Always‑on instructions | `.github/copilot-instructions.md` |
| Custom agents | `.claude/agents/*.agent.md` |
| Prompt files | `.agents/prompts/*.prompt.md` |
| Skills | `.claude/skills/*/SKILL.md` |
| Universal rules | `.agents/core/` |
| Tech‑stack guidelines | `.agents/stack/` |
| MCP servers | `.vscode/mcp.json` |
| Hooks | `.github/hooks/*.json` |

## Key Principles

1. All rules are stored in `.agents/` (the source of truth).
2. Use the `_bmad/` methodology for multi‑agent delivery workflows.
3. All schema/rule files use command‑format (actionable rules, no prose).
4. "Never Do" blocklist at the bottom of each rule file.
