# Bellosoft Delivery OS — Always-On Instructions

This file is loaded automatically by Copilot on every chat session. It provides the universal context for all AI interactions.

## Architecture

```
LAYER 1  .agents/core/             → company core: coding standards, processes, checklists, rules, patterns
LAYER 2  .agents/stack/            → Tech-specific guidelines: .NET, Vue, SQL, Azure, Docker
LAYER 3  .agents/skills/           → Agent skills: BMAD, GitHub management, Plane issue tracking, frontend design, Microsoft docs, TDD
LAYER 4  .agents/agents/           → Custom agents: architect, code, debug, ask, pm, review, sales
LAYER 5  docs/                     → project context: specs, architecture, memory
```

## Knowledge Base

All rules are stored in `.agents/` — Copilot-native, no vendor abstraction layer.

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

Seven specialized agents in `.claude/agents/`: architect, code, debug, ask, pm, review, sales.

## Key Principles

1. All rules are stored in `.agents/` — Copilot-native, no vendor abstraction layer
2. Use `_bmad/` methodology for multi-agent delivery workflows
3. All schema/rule files use command-format (actionable rules, no prose)
4. "Never Do" blocklist at the bottom of each rule file
