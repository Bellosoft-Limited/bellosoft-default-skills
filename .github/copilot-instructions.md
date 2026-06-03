# Copilot Instructions

This file is always loaded. Details live in `AGENTS.md`.

## Core Principles

- **Load on demand** — never pre-load rules; fetch only what the current task needs
- **Delegate complex work** — use agents for multi-step tasks, skills for domain rules
- **Lean context** — summarise completed sections to keep the window clean

## How to Work

1. Check `AGENTS.md` for the directory map and discovery commands
2. Load what you need — `skill` tool for skills, `read` for stack/core files
3. Delegate complex work via `task`

## Key Paths

| Resource | Path |
|---|---|
| Agent catalog | `AGENTS.md` |
| Skills | `.claude/skills/` |
| MCP config | `.vscode/mcp.json` |
