# Bellosoft — Always-On Instructions

Loaded automatically every session. Keep this minimal.

## Structure

| Location | Contents |
|---|---|
| `.agents/core/` | Universal rules: coding standards, git, security, testing, delivery |
| `.agents/stack/` | Tech-specific guidelines: .NET, Vue, SQL, Azure, Docker |
| `.agents/prompts/` | Reusable prompt templates |
| `.claude/skills/` | Skill manifests — load on demand via `skill` tool |
| `.claude/agents/` | Agent definitions — delegate via `task` tool |

## Key Rule

Load only what the current task needs. Do not pre-load stack or core files speculatively.
