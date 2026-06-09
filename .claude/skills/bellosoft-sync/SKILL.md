---
name: bellosoft-sync
description: >
  Tracker synchronisation layer for the bellosoft ecosystem. Handles import (pull
  existing tracker project into docs/planning-artifacts/), push (send planning
  artifacts to tracker), pull (refresh local state), migrate (move all issues from
  Plane → Jira or Jira → Plane), and update (transition a single ticket — called by
  dev-review, dev-execute, bellosoft-github). Triggers: /bellosoft-sync, "sync
  tracker", "import from jira", "import from plane", "migrate plane to jira",
  "migrate jira to plane", "push to tracker", "pull tracker state".
---

# Skill: bellosoft-sync

**This is the tracker synchronisation layer for the bellosoft ecosystem.**

All bellosoft skills that need to read or write tracker state delegate here.
This skill delegates ALL Plane operations to `bellosoft-plane` and ALL Jira
operations to `bellosoft-jira`. It never calls Plane MCP tools or Jira MCP
tools directly.

```
/bellosoft-sync import              ← pull tracker → docs/planning-artifacts/
/bellosoft-sync pull                ← refresh local sprint/status from tracker
/bellosoft-sync push                ← push docs/planning-artifacts/epics.md → tracker
/bellosoft-sync migrate             ← move all issues Plane→Jira or Jira→Plane
/bellosoft-sync update [id] [status] ← transition one ticket (called by other skills)
```

---

## Step 1 — Detect tracker

**Before any operation, resolve which tracker is active.**

```bash
cat docs/planning-artifacts/status.md 2>/dev/null | grep "^tracker:"
```

Resolution order:
1. `docs/planning-artifacts/status.md` has `tracker: jira` or `tracker: plane` → use it
2. Check `docs/planning-artifacts/jira-profile.md` exists → likely Jira
3. Check `docs/planning-artifacts/plane-profile.md` exists → likely Plane
4. Probe silently:
   - Try `mcp__atlassian__jira_get_myself` — if succeeds → Jira available
   - Try `mcp_plane_list_projects` — if succeeds → Plane available
5. Both available → ask: "Both Jira and Plane are connected. Which tracker? [jira/plane]"
6. One available → use it; save to `docs/planning-artifacts/status.md`
7. Neither → stop: "❌ No tracker connected. Run /bellosoft-jira setup or /bellosoft-plane setup first."

---

## Operation: IMPORT

**Purpose:** Bootstrap `docs/planning-artifacts/` from an existing tracker project.
Use this instead of `/bellosoft-plan-epics` when tickets already exist in Jira or Plane.

### When docs/planning-artifacts/ already has content

If `docs/planning-artifacts/epics.md` exists, ask before overwriting:
```
docs/planning-artifacts/epics.md already exists.
  a) Overwrite — replace entirely with tracker data
  b) Merge — add missing epics/stories, preserve manual additions
  c) Cancel
```

### Import flow

**For Jira:** Delegate to `bellosoft-jira import` which:
- Fetches all epics via JQL
- Fetches stories per epic
- Builds `docs/planning-artifacts/epics.md` in bellosoft format
- Updates `docs/planning-artifacts/status.md` and `jira-profile.md`

**For Plane:** Delegate to `bellosoft-plane import` which:
- Lists all modules/epics
- Lists all work items per module
- Builds `docs/planning-artifacts/epics.md` in bellosoft format
- Updates `docs/planning-artifacts/status.md` and `plane-profile.md`

### Output format

`docs/planning-artifacts/epics.md` must follow bellosoft format:

```markdown
# Epic Register — {Project Name}

_Source: imported from {Jira PROJ / Plane project} on {date}_

---

## Epic 1 — {Title}

**Tracker ID:** {PROJ-5 / plane-uuid}
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
2. **For Jira:** Delegate to `bellosoft-jira list-sprint` → update sprint snapshot in `status.md`
3. **For Plane:** Delegate to `bellosoft-plane list-sprint` → update cycle snapshot in `status.md`
4. Show diff: tickets that changed status since last pull

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
3. **For Jira:** Delegate to `bellosoft-jira sync-epics`
4. **For Plane:** Delegate to `bellosoft-plane sync-epics`
5. Report: created / updated / skipped / failed counts

---

## Operation: MIGRATE

**Purpose:** Copy all issues from one tracker to another (Plane→Jira or Jira→Plane).

### Step M1 — Confirm direction

If not specified, ask:
```
Which direction?
  a) Plane → Jira
  b) Jira → Plane
```

### Step M2 — Load source data

**Plane → Jira:** Delegate to `bellosoft-plane import` to fetch structured snapshot.
**Jira → Plane:** Delegate to `bellosoft-jira import` to fetch structured snapshot.

### Step M3 — Show migration plan before creating anything

```
Migration: Plane → Jira (MPWA)

  Epics:    8  (to create)
  Stories: 36  (to create)
  Tasks:    0  (none in source — run /bellosoft-plan-epic first to add tasks)

  Status mapping:
    Plane Done       → Jira Done  (transition applied after creation)
    Plane In Review  → Jira In Review
    Plane Started    → Jira In Progress
    Plane Unstarted  → Jira To Do
    Plane Backlog    → Jira Backlog
    Plane Cancelled  → Jira Won't Do (confirm: include or skip?)

Proceed? [y/n]
```

### Step M4 — Create in destination

**Plane → Jira:**
1. For each epic: delegate to `bellosoft-jira create-epic`
2. For each story: delegate to `bellosoft-jira create-story` with epic link
3. For each task: delegate to `bellosoft-jira create-task` with story parent
4. For Done items: apply Done transition immediately after creation
5. Label all created items `ai-generated`

**Jira → Plane:**
1. For each epic: delegate to `bellosoft-plane create-epic`
2. For each story/task: delegate to `bellosoft-plane create-story/create-task`
3. Match status via state mapping above

### Step M5 — Report and update status.md

```
✅ Migration complete
  Created: 8 epics, 36 stories, N tasks
  Done transitions applied: 9 items
  Failed: 0
```

Update `docs/planning-artifacts/status.md`:
```yaml
tracker: jira
migrated_from: plane
migration_date: {ISO date}
```

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
2. **For Jira:** Delegate to `bellosoft-jira update {ticket-id} transition "{status}"`
   and optionally `bellosoft-jira update {ticket-id} comment "{text}"`
3. **For Plane:** Delegate to `bellosoft-plane update {ticket-id} state "{status}"`
   and optionally `bellosoft-plane update {ticket-id} comment "{text}"`
4. Confirm: `✅ {ticket-id} → {status}`

---

## Hard rules

- **Never call `mcp__atlassian__*` or `mcp_plane_*` directly.** Route through `bellosoft-jira` or `bellosoft-plane`.
- **Never ask for credentials.** Credential resolution is the delegate skills' responsibility.
- **Always run Step 1 before any operation.** Never assume which tracker is active.
- **Preserve statuses on migrate.** Done items must be transitioned to Done in the destination.
- **Ask before overwriting** `docs/planning-artifacts/epics.md` if it already exists.

---

## Operation: REPLAN-AND-MIGRATE

**Purpose:** Full end-to-end workflow for teams migrating from one tracker to another
AND wanting to replan tickets in the Bellosoft format (proper epic → story → task hierarchy).
Use this when existing tickets are in a different format (e.g. BMAD, flat list, no sub-tasks)
and you want to produce a properly structured plan before pushing to the destination tracker.

```
/bellosoft-sync replan-and-migrate
```

### When to use this vs MIGRATE

| Use MIGRATE if… | Use REPLAN-AND-MIGRATE if… |
|-----------------|---------------------------|
| Existing tickets are already in Bellosoft format | Tickets are in BMAD or another format |
| Stories already have task breakdowns | Stories have no tasks (need decomposition) |
| You just want a 1:1 copy in the new tracker | You want to restructure as part of the migration |
| Speed matters more than quality | Quality of task breakdown matters |

### Step R1 — Confirm scope

```
Replan-and-migrate workflow

This will:
  1. Import existing tickets from {source tracker} into docs/planning-artifacts/
  2. Re-run /bellosoft-plan-epics to update the epic register with codebase cross-references
  3. Run /bellosoft-plan-epic on each epic to add task breakdowns
  4. Migrate everything to {destination tracker} with correct statuses

Source:      [Plane / Jira — auto-detected or ask]
Destination: [Jira / Plane — ask if not specified]

This is interactive — you'll review and approve at each planning step.
Estimated time: 15–30 min depending on number of epics.

Proceed? [y/n]
```

### Step R2 — Import from source

Delegate to `bellosoft-sync import` with the source tracker.
After import, `docs/planning-artifacts/epics.md` will reflect the current tracker state.

If `docs/planning-artifacts/epics.md` already exists and looks current → skip re-import,
ask: "docs/planning-artifacts/epics.md already exists. Re-import from tracker or use existing? [re-import/use-existing]"

### Step R3 — Refresh epic register (bellosoft-plan-epics)

Run the `bellosoft-plan-epics` planning workflow:
- Load codebase audit if available
- Cross-reference each epic with the audit (show what's already built)
- Present updated epic register for approval
- User can modify epic boundaries, priorities, remove epics for done features

**Do not skip this step.** The goal is to restructure the plan, not just copy it.
Pause and wait for the user to approve the epic register before continuing.

### Step R4 — Decompose each epic (bellosoft-plan-epic)

For each approved epic, run `bellosoft-plan-epic [Epic ID]`:
- Break stories into atomic, implementable tasks
- Each task should be ~2–4h of work
- Preserve Done status: if the epic/story is Done in source, mark tasks as Done too

Process epics one at a time. After each epic is decomposed, ask:
`"Epic E{N} decomposed into {N} stories / {N} tasks. Continue to E{N+1}? [y/n/skip]"`

### Step R5 — Final migration preview

Before pushing anything to the destination tracker, show the full migration plan:

```
Migration preview: {source} → {destination}

  Epics:      N   (N already Done — will be transitioned after creation)
  Stories:    N   (N Done, N In Progress, N To Do)
  Tasks:      N   (N Done)

  Label: ai-generated will be applied to all created items.

  Items with Done status in source:
    [EPIC-1] User Authentication → Done
    [EPIC-1-S2] Login flow → Done
    ...

Ready to create? [y/n]
```

### Step R6 — Create in destination

Delegate to `bellosoft-sync migrate` (Step M4) with the planned data.
- Create epics → stories → tasks in order
- Apply Done transitions immediately after creating Done items
- Report progress as items are created

### Step R7 — Report

```
✅ Replan-and-migrate complete

  Source:      Plane (bellosoft / metasis-pwa)
  Destination: Jira (MPWA)

  Created: N epics, N stories, N tasks
  Done transitions applied: N items
  Failed: N (see below for manual steps)

docs/planning-artifacts/status.md updated with new tracker preference.

Next: /bellosoft-sprint to see your active sprint in the new tracker.
```
