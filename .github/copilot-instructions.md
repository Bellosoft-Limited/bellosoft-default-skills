# Copilot Instructions — Bellosoft Delivery OS

## Knowledge Base

This repository provides company-wide defaults that sync into every client project using `scripts/sync.ps1` or `scripts/sync.sh`.

### `core/` — Universal Rules (always active)
- `coding-standards.md` — C#, TypeScript/Vue, Python naming & language rules
- `review-checklist.md` — PR review with 🔴 BLOCKER · 🟡 MAJOR · 🔵 MINOR · 💡 NIT
- `security-rules.md` — OWASP Top 10 + API Security Top 10 rules
- `git-flow.md` — GitFlow branching: main + develop + feature/* + hotfix/* + release/*
- `delivery-process.md` — Sprint lifecycle, Definition of Ready/Done
- `github-actions.md` — Workflows, OIDC, permissions, secrets, branch protection
- `testing-patterns.md` — TDD (Red-Green-Refactor), FIRST, AAA, xUnit patterns

### `stack/` — Tech-Specific Guidelines (context-dependent)
- `dotnet.md` — .NET 9/10, ASP.NET Core, EF Core conventions
- `vue.md` — Vue 3 Composition API, Nuxt 3, Pinia, TypeScript
- `mssql.md` — SQL Server 2022+, T-SQL, indexing, performance
- `postgresql.md` — PostgreSQL 16+, PL/pgSQL, indexing, performance
- `mariadb.md` — MariaDB 11.x, MySQL 8.0, InnoDB, Galera Cluster
- `azure.md` — Azure PaaS, naming, tagging, IAM, Key Vault, networking
- `docker.md` — Multi-stage builds, Docker Compose, security, CI

## Custom Agents

Seven specialized agents — defined as `.agent.md` files in `.github/agents/`:
- `architect.agent.md` — System architecture & memory bank
- `code.agent.md` — Feature implementation & debugging
- `debug.agent.md` — Issue analysis & root-cause fixing
- `ask.agent.md` — Project Q&A & knowledge retrieval
- `pm.agent.md` — Sprint planning & work item management
- `review.agent.md` — Adversarial code review & quality gates
- `sales.agent.md` — Proposals, estimates & client docs

## Copilot Configuration

| Customization | Copilot (VS Code) |
|---|---|
| Always-on instructions | `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` |
| Custom agents | `.github/agents/*.agent.md` |
| Prompt files | `.github/prompts/*.prompt.md` |
| Skills | `.github/skills/*/SKILL.md` |
| Universal rules | `.github/core/` |
| Tech-stack guidelines | `.github/stack/` |
| MCP servers | `.vscode/mcp.json` |
| Hooks | `.github/hooks/*.json` |

## Key Principles

1. All rules are stored in `.github/` — Copilot-native, no vendor abstraction layer
2. Use `_bmad/` methodology for multi-agent delivery workflows
3. All schema/rule files use command-format (actionable rules, no prose)
4. "Never Do" blocklist at the bottom of each rule file
