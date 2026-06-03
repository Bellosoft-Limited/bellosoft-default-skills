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
