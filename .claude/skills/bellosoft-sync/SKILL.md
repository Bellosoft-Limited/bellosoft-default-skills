---
name: bellosoft-sync
description: >
  Tracker synchronisation layer for the bellosoft ecosystem. Handles import (pull
  existing tracker project into docs/planning-artifacts/), push (send planning
  artifacts to tracker), pull (refresh local state), migrate (move all issues from
  one tracker to another, e.g. Jira ↔ OpenProject), and update (transition a single
  ticket — called by dev-review, dev-execute, bellosoft-github). Triggers:
  /bellosoft-sync, "sync tracker", "import from jira", "push to tracker",
  "pull tracker state", "migrate to another tracker".
---

# Skill: bellosoft-sync

**This is the tracker synchronisation layer for the bellosoft ecosystem.**

All bellosoft skills that need to read or write tracker state delegate here.
This skill delegates ALL tracker operations to the matching `bellosoft-<tracker>` skill
(`bellosoft-jira` is the default; `bellosoft-openproject` also exists). It never calls
tracker MCP tools or APIs directly. Where this file says `bellosoft-jira`, use the
skill of the active tracker.

```
/bellosoft-sync import              ← pull tracker → docs/planning-artifacts/
/bellosoft-sync pull                ← refresh local sprint/status from tracker
/bellosoft-sync push                ← push docs/planning-artifacts/epics.md → tracker
/bellosoft-sync migrate             ← move all issues from one tracker to another
/bellosoft-sync replan-and-migrate  ← migrate AND restructure into bellosoft format
/bellosoft-sync update [id] [status] ← transition one ticket (called by other skills)
```

---

## Step 1 — Detect tracker

**Before any operation, resolve which tracker is active.**

```bash
cat docs/planning-artifacts/status.md 2>/dev/null | grep "^tracker:"
```

Resolution order:
1. `docs/planning-artifacts/status.md` has `tracker: <name>` and a `bellosoft-<name>` skill exists → use it
2. Check `docs/planning-artifacts/jira-profile.md` exists → likely Jira
3. Probe silently: try `mcp__atlassian__jira_get_myself` — if succeeds → Jira available
4. Available → use it; save to `docs/planning-artifacts/status.md`
5. Not available → stop: "❌ No tracker connected. Run /bellosoft-jira setup first."

---

## Operation: IMPORT

**Purpose:** Bootstrap `docs/planning-artifacts/` from an existing tracker project.
Use this instead of `/bellosoft-plan-epics` when tickets already exist in Jira.

### When docs/planning-artifacts/ already has content

If `docs/planning-artifacts/epics.md` exists, ask before overwriting:
```
docs/planning-artifacts/epics.md already exists.
  a) Overwrite — replace entirely with tracker data
  b) Merge — add missing epics/stories, preserve manual additions
  c) Cancel
```

### Import flow

Delegate to `bellosoft-jira import` which:
- Fetches all epics via JQL
- Fetches stories per epic
- Builds `docs/planning-artifacts/epics.md` in bellosoft format
- Updates `docs/planning-artifacts/status.md` and `jira-profile.md`

### Output format

`docs/planning-artifacts/epics.md` must follow bellosoft format:

```markdown
# Epic Register — {Project Name}

_Source: imported from {Jira PROJ} on {date}_

---

## Epic 1 — {Title}

**Tracker ID:** {PROJ-5}
**Status:** {To Do / In Progress / Done}
**Goal:** {one-sentence goal}

### Story 1.1 — {Title}

**Tracker ID:** {PROJ-12}
**Status:** {status}
**Goal:** {one sentence}
**Acceptance Criteria:**
- [ ] {AC 1}
- [ ] {AC 2}
```

---

## Operation: PULL

**Purpose:** Refresh `docs/planning-artifacts/status.md` with latest sprint state.

Steps:
1. Detect tracker (Step 1)
2. Delegate to `bellosoft-jira list-sprint` → update sprint snapshot in `status.md`
3. Show diff: tickets that changed status since last pull

Output appended to `docs/planning-artifacts/status.md`:
```
last_pull: {ISO datetime}
sprint_state:
  in_progress: [PROJ-12, PROJ-15]
  done: [PROJ-10, PROJ-11]
  blocked: []
```

---

## Operation: PUSH

**Purpose:** Push `docs/planning-artifacts/epics.md` to the active tracker.
Creates missing epics/stories/tasks; updates changed ones; skips up-to-date items.

Steps:
1. Detect tracker (Step 1)
2. Read `docs/planning-artifacts/epics.md`
3. Delegate to `bellosoft-jira sync-epics`
4. Report: created / updated / skipped / failed counts

---

## Operation: UPDATE

**Purpose:** Transition a single tracker ticket and optionally add a comment.
Called by: `bellosoft-dev-review`, `bellosoft-dev-execute`, `bellosoft-github`.

Usage (from other skills):
```
→ bellosoft-sync: update {ticket-id} "{new status}" comment="{optional text}"
```

Steps:
1. Detect tracker (Step 1)
2. Delegate to `bellosoft-jira update {ticket-id} transition "{status}"`
   and optionally `bellosoft-jira update {ticket-id} comment "{text}"`
3. Confirm: `✅ {ticket-id} → {status}`

---

## Operation: MIGRATE

**Purpose:** Copy all issues from one tracker to another. Works with any pair of trackers
that have a `bellosoft-<name>` integration skill (today: `jira`, `openproject`).

### Tracker contract

A tracker can be a migration source or destination if its skill supports:
- Source: `import` (returns epics, stories, tasks with status and hierarchy)
- Destination: `create-epic`, `create-story`, `create-task`, `update ... transition`

### Tracker without an integration skill

For a tracker with no `bellosoft-<name>` skill (retired or new tool), use a file as the source:
1. Ask the dev to export issues from the old tool (CSV or JSON).
2. Map the export to `docs/planning-artifacts/epics.md` (bellosoft format) with the dev.
   Confirm the column mapping before writing: id, title, type, parent, status, description, ACs.
3. Continue at Step M3 as if the import had just run.

If the destination has no skill, stop. Create the integration skill first.

### Step M1 — Confirm direction

If not specified, ask:
```
Migrate from which tracker to which? (e.g. openproject → jira)
```
Source and destination must differ.

### Step M2 — Load source data

Delegate to `bellosoft-<source> import` to get a structured snapshot (or use the file from above).

### Step M3 — Show migration plan before creating anything

```
Migration: {source} → {destination} ({project})

  Epics:    N  (to create)
  Stories:  N  (to create)
  Tasks:    N  (none in source — run /bellosoft-plan-epic first to add tasks)

  Status mapping:
    {source state}  → {destination state}
    ...
    {cancelled state} → {destination state} (confirm: include or skip?)

Proceed? [y/n]
```

Build the status mapping from the canonical set: Backlog, To Do, In Progress, In Review, Done, Cancelled.
Map each tracker state to the closest canonical state, then to the destination state.
Show unmapped states to the dev and ask. Never guess.

### Step M4 — Create in destination

1. For each epic: delegate to `bellosoft-<destination> create-epic`
2. For each story: `create-story` with epic link
3. For each task: `create-task` with story parent
4. For Done items: apply Done transition right after creation
5. Label all created items `ai-generated`

### Step M5 — Report and update status.md

```
✅ Migration complete
  Created: N epics, N stories, N tasks
  Done transitions applied: N items
  Failed: N
```

Update `docs/planning-artifacts/status.md`:
```yaml
tracker: {destination}
migrated_from: {source}
migration_date: {ISO date}
```

---

## Operation: REPLAN-AND-MIGRATE

**Purpose:** Migrate AND restructure tickets into bellosoft format (epic → story → task).
Use when existing tickets are flat, in another format (e.g. BMAD), or have no sub-tasks.

```
/bellosoft-sync replan-and-migrate
```

| Use MIGRATE if… | Use REPLAN-AND-MIGRATE if… |
|-----------------|---------------------------|
| Tickets are already in bellosoft format | Tickets are in another format |
| Stories already have tasks | Stories have no tasks |
| You want a 1:1 copy | You want to restructure during the move |
| Speed matters most | Task quality matters most |

### Step R1 — Confirm scope

```
Replan-and-migrate: {source} → {destination}

  1. Import tickets from {source} into docs/planning-artifacts/
  2. Refresh the epic register (/bellosoft-plan-epics)
  3. Decompose each epic (/bellosoft-plan-epic)
  4. Migrate to {destination} with statuses kept

Interactive. You approve each planning step. About 15–30 min.
Proceed? [y/n]
```

### Step R2 — Import from source

Run `import` for the source tracker (or file export, see MIGRATE).
If `docs/planning-artifacts/epics.md` exists, ask: `Re-import or use existing? [re-import/use-existing]`

### Step R3 — Refresh epic register

Run `bellosoft-plan-epics`. Cross-reference with the codebase audit if present.
**Do not skip.** Wait for the dev to approve the register.

### Step R4 — Decompose each epic

For each approved epic, run `bellosoft-plan-epic [Epic ID]`.
- Tasks of about 2–4 h each.
- Done in source → Done tasks.
- One epic at a time. After each, ask: `Epic E{N}: N stories, N tasks. Continue to E{N+1}? [y/n/skip]`

### Step R5 — Preview, create, report

Show the full plan (counts per status, Done items list) and ask `Ready to create? [y/n]`.
Then run MIGRATE Step M4 and M5 with the planned data.
End with: `Next: /bellosoft-sprint to see the active sprint in the new tracker.`

---

## Hard rules

- **Never call tracker MCP tools or APIs directly** (e.g. `mcp__atlassian__*`). Route through the tracker's `bellosoft-<tracker>` skill.
- **Never ask for credentials.** Credential resolution is the delegate skills' responsibility.
- **Always run Step 1 before any operation.** Never assume which tracker is active.
- **Ask before overwriting** `docs/planning-artifacts/epics.md` if it already exists.
- **Preserve statuses on migrate.** Done items must be transitioned to Done in the destination.
