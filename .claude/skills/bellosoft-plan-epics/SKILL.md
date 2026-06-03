---
name: bellosoft-plan-epics
description: >
  Use this skill to start planning from a PRD, update an existing plan when the PRD
  changes, or import an existing plan from Jira/Plane. Triggers: /bellosoft-plan-epics,
  "identify epics", "parse this PRD", "PRD changed", "update epics", "re-read the PRD".
  For teams already in Jira/Plane without a PRD, use /bellosoft-sync import instead —
  it bootstraps docs/planning-artifacts/ directly from the tracker. Does NOT decompose stories or tasks
  — that is /bellosoft-plan-epic. Run this first, or re-run whenever the PRD changes.
---

# Skill: plan-epics

## Purpose
Read a PRD and produce an **epic register** — the high-level map of what needs to
be built. This is the entry point for the entire planning workflow. Run it once at
the start, then re-run it whenever the PRD changes.

---

## Invocation

```
/bellosoft-plan-epics [path/to/prd.md]     ← new PRD
/bellosoft-plan-epics                       ← re-reads PRD from docs/planning-artifacts/prd-source.md if saved
```

> **Already have tickets in Jira/Plane?** Skip this skill and run `/bellosoft-sync import` instead.
> It bootstraps `docs/planning-artifacts/` from your existing tracker project — no PRD needed.

---

## Step 1 — Load Codebase Audit (if project exists)

Before reading the PRD, run these checks in order:

```bash
# 1. Check for existing audit
cat docs/planning-artifacts/codebase-audit.md 2>/dev/null | head -5

# 2. Get audit file age (if it exists)
stat docs/planning-artifacts/codebase-audit.md 2>/dev/null

# 3. Count files changed since audit was written
# (proxy: files newer than the audit file)
find . -newer docs/planning-artifacts/codebase-audit.md \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/bin/*' \
  -not -path '*/obj/*' \
  -not -path '*/docs/planning-artifacts/*' \
  -name "*.cs" -o -name "*.ts" -o -name "*.vue" \
  2>/dev/null | wc -l

# 4. Check if there is source code at all
find . -maxdepth 3 \( -name "*.csproj" -o -name "package.json" \
  -o -name "*.sln" -o -name "go.mod" \) 2>/dev/null | head -5
```

**Four scenarios:**

---

**A) No source code found → Greenfield project**
Proceed directly to Step 2. No audit needed.

---

**B) Source code exists, no audit at all**
```
⚠️  No codebase audit found — this looks like an existing project.

Planning without an audit risks:
  - Creating epics for things already built
  - Ignoring partial implementations
  - Missing established conventions

Options:
  1. Run /bellosoft-audit-codebase now (recommended — ~2-5 min)
  2. Skip and plan from PRD only

Which would you prefer?
```
If option 2 chosen → add visible warning to all output:
`⚠️ No audit — epics may overlap with existing implementation.`

---

**C) Audit exists but is stale**

Audit is considered **stale** if ANY of these are true:
- Audit file is older than **14 days**
- More than **20 source files** have been modified since the audit was written
- The audit's `**Audited:**` date header is older than the last entry in `docs/planning-artifacts/status.md`
  (meaning sprints have been delivered since the audit — implementation has moved on)

If stale, show:
```
⚠️  Codebase audit is outdated.

  Audited:        [date from audit header]
  Days since:     N days ago
  Files changed:  N source files modified since audit

  The audit may no longer reflect what's actually implemented.
  Epics could be planned against stale status (e.g. marking
  something as 🔶 Partial that is now ✅ Complete).

Options:
  1. Re-run /bellosoft-audit-codebase first (recommended)
  2. Use stale audit anyway (I'll flag affected epics with ⚠️ Unverified)
  3. Skip audit entirely

Which would you prefer?
```
If option 2 chosen → mark every epic that references a non-greenfield module
with `⚠️ Based on stale audit — verify status before decomposing`.

---

**D) Audit exists and is fresh (< 14 days, < 20 files changed)**
Load silently. Proceed to Step 2.
Show a single line confirmation at the end of the output:
`ℹ️ Codebase audit from [date] used ([N] days old, [N] files changed since).`

---

## Step 2 — Load PRD

### 2a — Resolve the PRD path

**If a path is given:**

Check whether the file is in the correct location (`docs/prd/`):

- Path is already under `docs/prd/` → load it, proceed.
- Path is anywhere else (e.g. `docs/my-feature.md`, `prd.md`, `docs/planning-artifacts/prd.md`) → file is in the wrong place. Show:

```
⚠️  PRD found at [given path] — this should live under docs/prd/.

Before planning, I need to sort this out:
  1. Move and rename to docs/prd/YYYY-MM-DD-[feature-name].md (recommended)
  2. Copy (keep original in place, also register in docs/prd/)
  3. Use as-is without moving (planning will work, but docs/prd/ stays unorganised)

Also: does this PRD already exist in docs/prd/ under a different name?
```

Scan `docs/prd/` for files with similar names or overlapping content (compare titles/executive summaries). If a likely match is found:

```
⚠️  This looks similar to an existing PRD:
  docs/prd/2026-04-10-campaign-scheduling.md

Options:
  1. This is an amendment — merge as a new version (docs/prd/YYYY-MM-DD-campaign-scheduling-v2.md)
  2. This is a separate feature — save as a new file
  3. Replace the existing file entirely
```

After the user decides, perform the file operation (move/copy/rename) before proceeding.

**If no path is given:**

1. Scan `docs/prd/` for PRD files:
   ```bash
   find docs/prd/ -name "*.md" 2>/dev/null | sort -r | head -20
   ```
2. If files found → show the list and ask which to use, or offer "paste content / provide a path"
3. If `docs/planning-artifacts/prd-source.md` exists (from a previous run) → offer it as a fallback
4. If nothing found anywhere → ask: "Please provide the PRD path, drop a file in docs/prd/, or paste the content."

### 2b — Save canonical reference

Once the PRD is resolved and in `docs/prd/`, save a reference (not a copy) to `docs/planning-artifacts/prd-source.md`:

```markdown
# PRD Source Reference
**File:** docs/prd/YYYY-MM-DD-feature-name.md
**Loaded:** [today's date]
```

This keeps `docs/planning-artifacts/` lightweight — the PRD itself always lives in `docs/prd/`.

---

## Step 2c — Detect changes (if re-running)

If `docs/planning-artifacts/epics.md` already exists from a previous run:

1. Read the PRD path from `docs/planning-artifacts/prd-source.md`, load the actual PRD from `docs/prd/`
2. Compare the new PRD against the previously loaded version
2. Identify what changed:
   - New requirements added
   - Existing requirements modified
   - Requirements removed / descoped
3. Show a diff summary:

```
## PRD Changes Detected

### Added
- [New requirement or section]

### Modified
- [What changed in requirement X]

### Removed / Descoped
- [What was removed]

### Impact on existing epics
- Epic E2 likely affected by change to authentication requirements
- Epic E4 may be descoped entirely

Proceed to update epic register? (yes / no)
```

If no `docs/planning-artifacts/epics.md` exists → skip diff, proceed as first run.

---

## Step 3 — Extract structured info from PRD

Parse and identify:
- **Product / feature name**
- **Goal** — business outcome
- **Personas** — who uses this
- **Functional requirements** — numbered list
- **Non-functional requirements** — perf, security, compliance, scale
- **Integrations** — external APIs, services
- **Out of scope**
- **Open questions** — ambiguities needing a decision

---

## Step 4 — Surface open questions

Before proposing epics, raise blockers:

```
## ❓ Open Questions — [Product Name]

1. [Ambiguity that affects epic boundaries]
2. [Missing requirement that would create a new epic]
3. [Scope question that could merge or split epics]

Answer these or type "skip" to proceed with assumptions.
```

Document all assumptions when skipped.

---

## Step 5 — Identify Epics (cross-referenced with audit)

Group requirements into epics. Each epic is a **cohesive feature area** that can
be planned and delivered somewhat independently.

**If codebase audit is loaded**, for each candidate epic:
1. Check the audit's Module Inventory for matching modules
2. Classify the epic's starting point:

| Epic start | Meaning | Impact on estimate |
|------------|---------|-------------------|
| 🆕 Greenfield | Nothing exists | Full estimate |
| 🔶 Continue | Partially built — audit shows ~X% done | Reduce estimate proportionally; stories cover only the gap |
| 🔁 Rework | Built but wrong — tech debt or wrong pattern | Add rework tasks; estimate may be higher than greenfield |
| ✅ Already done | Fully implemented per audit | Do NOT create epic — document as complete |

Never create an epic for something the audit marks ✅ Complete.
Always note what already exists when starting point is 🔶 Continue.

**Epic sizing guide:**

| T-shirt | Hours | Sprints |
|---------|-------|---------|
| XS | < 16h | < 1 sprint |
| S | 16–40h | 1 sprint |
| M | 40–80h | 1–2 sprints |
| L | 80–160h | 2–4 sprints |
| XL | > 160h | needs splitting |

If an epic is XL → suggest splitting before proceeding.

---

## Step 6 — Output the Epic Register

```markdown
# Epic Register — [Product Name]
**PRD version:** [date of PRD / hash]
**Generated:** [today's date]
**Status:** Draft — awaiting approval

---

## Assumptions
- [Any assumption made due to skipped open questions]

---

| ID | Epic | Start | Size | Est (rough) | Priority | Status | Dependencies |
|----|------|-------|------|-------------|----------|--------|--------------|
| E1 | [Epic name] | 🆕 Greenfield | M | ~40h | High | 🔲 Not started | — |
| E2 | [Epic name] | 🔶 Continue (~40% done) | S | ~16h | High | 🔲 Not started | E1 |
| E3 | [Epic name] | 🔁 Rework | M | ~48h | Medium | 🔲 Not started | E1 |

---

### E1: [Epic Name]
**Goal:** [What this epic achieves for the user/business]
**Covers requirements:** [REQ-1, REQ-2, REQ-5]
**Starting point:** 🔶 Continue — `CampaignService` exists with Create/List; scheduling and send not implemented
**What already exists:** [specific files/classes/routes already built — from audit]
**What's missing:** [the gap that this epic will close]
**Rough estimate:** ~24h (reduced from ~40h because ~40% already built)
**Suggested sprint:** Sprint 1–2
**Conventions to follow:** [from audit — e.g. "use repository pattern, FluentValidation, ApiResponse<T> wrapper"]
**Notes:** [Any important context, risks, or constraints]

### E2: [Epic Name]
[... repeat ...]

---

## Suggested delivery order
1. E1 — foundation (auth, DB schema, core entities)
2. E2 — depends on E1 (core business logic)
3. E4 — independent, can be parallelised
4. E3 — largest, last

## Epics NOT yet decomposed into stories
All epics above are waiting for /bellosoft-plan-epic [E1|E2|...] to break them down.
```

---

## Step 7 — Approval gate

```
---
Epic register ready. N epics identified, ~Xh total.

Reply with:
  ✅ approve                  — save register, ready for /bellosoft-plan-epic
  ✏️  [feedback]              — adjust epic boundaries or priorities
  ➕ add epic: [description]  — add a missing epic
  ❌ cancel
```

---

## Step 8 — Save state (after approval)

Write `docs/planning-artifacts/epics.md` with the approved epic register.
Write `docs/planning-artifacts/prd-source.md` with the current PRD content.
Write `docs/planning-artifacts/status.md`:

```markdown
# Planning Status — [Product Name]

| Epic | Status | Stories created | Pushed to |
|------|--------|-----------------|-----------|
| E1: [name] | 🔲 Not started | 0 | — |
| E2: [name] | 🔲 Not started | 0 | — |
| E3: [name] | 🔲 Not started | 0 | — |
```

Then output:
```
✅ Epic register saved to docs/planning-artifacts/epics.md

Next steps:
  /bellosoft-plan-epic E1    ← decompose E1 into stories and tasks
  /bellosoft-plan-epic E2    ← decompose E2 (can be done later)
  /bellosoft-plan-epics      ← re-run if the PRD changes
```

---

## Hard rules
- Never create stories or tasks — that is /bellosoft-plan-epic
- Never push to Jira or Plane — that is /bellosoft-plan-epic
- Always save state before finishing
- Always detect PRD changes when re-running
