# Skill Customization Discovery
> Before starting any task, check `_bmad/custom/` for overrides matching your work domain

---

## Rule

At the start of every session (before loading any skill), scan `_bmad/custom/*.toml` for files whose skill name matches the work you are about to do. If a match exists, load the corresponding skill via the `skill` tool so its customizations (persistent facts, menus, activation hooks) take effect.

## Mapping

| TOML file | Skill to load | Work domain |
|---|---|---|
| `_bmad/custom/bmad-agent-dev.toml` | `bmad-agent-dev` | Story implementation, coding, bug fixing, code review patches, test writing |
| `_bmad/custom/<skill-name>.toml` | `<skill-name>` | Any work that matches the skill's purpose |

The mapping rule: strip `.toml` from the filename — the result is the skill name. Verify the skill exists under `.claude/skills/<skill-name>/SKILL.md` before loading.

## Procedure

1. Glob `_bmad/custom/*.toml` in the project root.
2. For each file, derive the skill name: `basename(filename, ".toml")`.
3. Check if `.claude/skills/{skill-name}/SKILL.md` exists.
4. If it does, decide whether the skill's domain matches your current task.
5. On match: `skill tool name="{skill-name}"` to load the skill and its customizations.

## Why

Customization files under `_bmad/custom/` define team-enforced rules (branch creation, commit format, PR conventions, TDD discipline). These rules only take effect when the corresponding skill is loaded. This discovery step ensures they are never skipped.

## What to Never Do

- Never start coding without checking `_bmad/custom/bmad-agent-dev.toml` first.
- Never assume a customization file is optional — treat all `_bmad/custom/*.toml` files as mandatory discovery prompts.
- Never skip loading a skill when its customization file exists and the work domain matches.
