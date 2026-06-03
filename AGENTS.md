# Agents and Skills Catalog

Index only — load on demand, never pre-load.

## Directory Map

| Resource | Path |
|---|---|
| Core instructions | `.claude/CLAUDE.md` |
| Skills | `.claude/skills/<name>/SKILL.md` |
| Agents | `.claude/agents/*.agent.md` |
| Stack guidelines | `.agents/stack/<name>.md` |
| Universal rules | `.agents/core/<name>.md` |
| Prompt templates | `.agents/prompts/<name>.prompt.md` |
| Tracker bootstrap | `.claude/skills/bellosoft-plane/references/tracker-bootstrap.md` |

## Discovery

```bash
skill                        # list all skills
ls .claude/agents/           # list agents
ls .agents/stack/            # list stack rules
ls .agents/core/             # list core rules
ls .agents/prompts/          # list prompt templates
```
