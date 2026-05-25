# Bellosoft Delivery OS — Always-On Instructions

This file is loaded automatically on every session. Keep it minimal.

## Project Structure

Rules and guidelines are organised under `.agents/`:

- `.agents/core/` — universal rules: coding standards, git flow, security, testing, delivery process
- `.agents/stack/` — tech-specific guidelines: .NET, Vue, SQL, Azure, Docker
- `.agents/instructions/` — always-on instruction files (this file)
- `.agents/prompts/` — reusable prompt templates

Skills and agents:

- `.claude/skills/` — skill manifests loaded on demand via `skill` tool
- `.claude/agents/` — custom agent definitions: architect, code, debug, ask, pm, review, sales

See `AGENTS.md` for the full directory map and loading instructions.

## Key Principles

- Load rules on demand — never pre-load `.agents/core/` or `.agents/stack/` upfront
- Check `_bmad/custom/bmad-agent-dev.toml` before any coding task
- Use `_bmad/` methodology for multi-agent delivery workflows