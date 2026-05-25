# Claude Code — Bellosoft Delivery OS

This file is always loaded. Keep it minimal — detailed references live in `AGENTS.md`.

## Core Principles

- **BMAD methodology** — use multi-agent workflows via `task` and `skill`
- **Load on demand** — never pre-load rules; fetch only what the current task needs
- **Delegate appropriately** — use agents for complex work, skills for domain rules
- **Lean context** — compress completed sections to keep the conversation window clean

## How to Work

1. Check `AGENTS.md` for the directory map and discovery commands
2. Check `_bmad/custom/bmad-agent-dev.toml` before any coding task
3. Load what you need — skill manifests via `skill`, plain files via `read`
4. Delegate complex work via `task`
5. Compress when a section of work is complete

## Loading Rules

**Skill manifests** (`.claude/skills/`) — use `skill` tool:
```bash
skill name="bmad-agent-dev"
skill name="bellosoft-github"
```

**Stack, core, and prompt files** — read directly:
```bash
read .agents/stack/dotnet.md
read .agents/core/security-rules.md
read .agents/prompts/github-pr.prompt.md
```

## Delegating Work

```bash
task subagent_type="code" prompt="Implement user login"
task subagent_type="review" prompt="Review PR #42"
```

## Reference

See `AGENTS.md` for:
- Full directory map
- How to discover available skills, agents, stack rules, and prompts
- Complete loading instructions