# Agents and Skills Catalog

This file is an index — not a loading instruction. Agents and skills are loaded on demand, only when relevant to the current task. Do not pre-load anything listed here.

## Directory Map

| Resource | Path | Type |
|---|---|---|
| Project instructions | `CLAUDE.md` | Always-on core context |
| This catalog | `AGENTS.md` | Reference index |
| Always-on instructions | `.agents/instructions/bellosoft-core.instructions.md` | Read automatically |
| Agent definitions | `.claude/agents/*.agent.md` | Loaded via `task` tool |
| Skill manifests | `.claude/skills/<name>/SKILL.md` | Loaded via `skill` tool |
| Tech-stack guidelines | `.agents/stack/<name>.md` | Read directly when needed |
| Universal rules | `.agents/core/<name>.md` | Read directly when needed |
| Prompt templates | `.agents/prompts/<name>.prompt.md` | Read directly when needed |
| Skill customisations | `_bmad/custom/<skill-name>.toml` | Read before loading matching skill |
| Settings | `.claude/settings.json` | Model config, env vars, permissions |
| Local settings | `.claude/settings.local.json` | User-specific overrides (git-ignored) |

## How to Discover

- **Skills:** run `skill` with no arguments to list all available skills under `.claude/skills/`
- **Agents:** inspect `.claude/agents/` for available agent manifests
- **Stack rules:** inspect `.agents/stack/` for available tech-stack files
- **Core rules:** inspect `.agents/core/` for available universal rule files
- **Prompts:** inspect `.agents/prompts/` for available prompt templates

## How to Load

**Skill manifests** — use the `skill` tool:
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

**Agents** — delegate via `task` tool:
```bash
task subagent_type="code" prompt="Implement user login feature"
task subagent_type="review" prompt="Review PR #42"
```

## Before Starting Any Task

Check `_bmad/custom/` for applicable overrides:

- `_bmad/custom/bmad-agent-dev.toml` — mandatory for story implementation
- Any other `.toml` matching a skill you are about to load