# Design — Bellosoft document skill

**Date:** 2026-08-06
**Status:** approved, implemented

## Problem

Two standalone HTML templates (EN/£, PT-BR/R$) carry the Bellosoft house design
for client-facing documents. They arrived as a zip and lived nowhere. The goal:
make them something Claude reaches for automatically, in Claude Code *and* in
claude.ai chat, whenever a Bellosoft document is wanted.

## Design decisions

**Portable skill, not a repo asset:** `~/.claude/skills/bellosoft-document/` makes
it available across projects and zips into claude.ai chat. Deliberately not in
APP-CONT-TICA (Contatica owns the repo; Bellosoft brand assets belong elsewhere).

**Templates as supplied, minus one blocking fix:** see *Fixed on intake* below;
nothing else changed. The specimen document inside each template serves as the
canonical block reference, eliminating sync drift and keeping the rule "delete
unused, invent none" literally true.

**Three output formats:** HTML (the source), PDF (headless-rendered), DOCX (a
re-creation, lossy). Always ask; never assume.

**No presets:** Generic blocks only. Presets (proposal, SoW) were rejected as
unearned; the thirteen blocks compose well without them.

## Structure

- **SKILL.md** — trigger, workflow, block reference, and hard rules; always loaded
- **assets/** — locale templates (EN, PT-BR), as supplied minus one blocking fix
- **references/house-style.md** — voice, typography, locale rules; load when writing copy
- **references/docx.md** — Word format constraints; load only for `.docx` output

The specimen document inside each template is the canonical block reference; there
is no separate list to drift out of sync.

## Fixed on intake

Both supplied templates were broken and rendered nothing. The `<doc-page>`
engine's JSDoc comment contains two illustrative usage lines carrying a literal
`</script>` (lines 78 and 100). The HTML parser does not read JavaScript
comments — the first of those closes the `<script>` element early, so the rest
of the engine renders as visible page text, the custom element is never defined,
and `doc-page:not(:defined){visibility:hidden}` hides the document itself.

Fix: escape the slash to `<\/script>` on those two lines in each template. Inside
a comment this changes no behaviour. Verified by rendering both locales.

Anyone regenerating these templates upstream should apply the same escape at
source, or the next copy arrives broken again.

## Known limits

See `SKILL.md` (sections 2, 96–110) and `references/docx.md` for operational
constraints and mitigations:

- **DOCX cannot match** the HTML design. Typography, hairlines, and the `<doc-page>`
  paging engine do not carry over.
- **PDF rendering** requires a headless browser; not available in all sandboxes.
- **Google Fonts is a network dependency.** Offline fallback is present but visually
  degraded; embedding the font (~200KB per document) was considered and rejected.
