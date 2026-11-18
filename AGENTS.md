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
| Tracker bootstrap | `.claude/skills/bellosoft-jira/references/tracker-bootstrap.md` |
| Matt Pocock skills (vendored, don't edit) | `.claude/vendor/mattpocock-skills/README.md` |

## Discovery

```bash
skill                        # list all skills
ls .claude/agents/           # list agents
ls .agents/stack/            # list stack rules
ls .agents/core/             # list core rules
ls .agents/prompts/          # list prompt templates
```

## Agent skills

Issue tracker, triage labels, branch/PR conventions and domain docs for the Matt Pocock skills are defined in `.claude/CLAUDE.md` → "Agent skills". Read that section; it is the single source of truth.
