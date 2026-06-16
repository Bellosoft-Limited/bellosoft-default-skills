---
name: bellosoft-sprint
description: >
  Sprint-level awareness for developers. Shows what's open in the current sprint,
  assigned to the current user or the team. Entry point for the dev daily workflow.
  Triggers: /bellosoft-sprint, "what's in my sprint", "what should I work on",
  "show my tickets", "what's open this sprint", "morning standup", "what's left this sprint",
  "sprint status", "what are my stories". Fetches live data from Jira or Plane via MCP.
  Falls back to docs/planning-artifacts/status.md if no tracker is connected.
---

# Skill: bellosoft-sprint

Sprint-level view for developers. Answers "what should I work on?" and connects
directly into the dev workflow skills.

```
/bellosoft-sprint            ← my open stories this sprint
/bellosoft-sprint team       ← full team sprint board
/bellosoft-sprint [ID]       ← specific sprint or cycle by name/ID
```

---

## Step 0 — Load epic context for the current sprint

Before fetching tracker state, load the planning artifacts to understand what was *intended*
for the epics active in this sprint. This surfaces scope drift and course changes early.

1. Read `docs/planning-artifacts/epics.md` — get the epic register (IDs, titles, status)
2. Identify which epics are **In Progress** (status: `active` or equivalent)
3. For each active epic, check if `docs/planning-artifacts/epic-plans/E{N}-plan.md` exists
   - If it does, read it and extract: total stories planned, stories marked done, any notes
4. After fetching the sprint board in Step 1, compare planned vs actual:
   - Stories in sprint not in the epic plan → scope was added after planning
   - Stories in epic plan not yet started but epic is nearly done → may be missing from sprint
   - Epic plan notes indicating changed direction → flag explicitly

If no `docs/planning-artifacts/` folder exists, skip this step silently.

---

## Step 1 — Detect tracker and sprint

**Plane — delegate to `/bellosoft-plane`:**
```
/bellosoft-plane list-sprint mine    ← your open stories
/bellosoft-plane list-sprint team    ← full team view
```
bellosoft-plane handles pagination, active cycle detection, and grouping.

**Jira — delegate to `/bellosoft-jira`:**
```
/bellosoft-jira list-sprint mine    ← your open stories
/bellosoft-jira list-sprint team    ← full team view
```
bellosoft-jira handles JQL construction, field parsing, and status grouping.

**If no tracker MCP connected:**
Read `docs/planning-artifacts/status.md` and filter for the current sprint.
Note: `⚠️ No tracker connected — showing local plan state, which may be stale. Run /bellosoft-sync pull to refresh.`

---

## Step 2 — Filter and display

Default view: issues assigned to current user that are not Done.
`team` flag: show all assignees.

```
## Sprint [N] — [Sprint name]  ([start] → [end])

### 🔴 Blocked
| Ticket | Title | Blocked by |
|--------|-------|-----------|
| PROJ-44 | [title] | PROJ-38 (not merged) |

### 🟡 In Progress
| Ticket | Title | Assignee | Days in state |
|--------|-------|----------|--------------|
| PROJ-42 | [title] | @you | 2d |

### ⚪ To Do (your stories)
| Ticket | Title | Size | Priority |
|--------|-------|------|---------|
| PROJ-43 | [title] | S | High |
| PROJ-45 | [title] | M | Medium |

### ✅ Done this sprint
[N stories completed]

---
Sprint progress: N/N stories | Xh remaining | [N] days left
```

If Step 0 found any drift between the epic plan and the sprint, add a **Course changes** section
after the board:

```
### ⚠️ Epic scope changes detected

**E3 — [Epic title]**
- E3-S4 "[story title]" is in the epic plan but not in this sprint — was it postponed?
- PROJ-51 is in sprint but not in the epic plan — scope was added after planning

**E5 — [Epic title]**
- Epic plan notes: "Authentication flow changed to OAuth-only in week 3"
  → Confirm implementation reflects this before closing remaining stories.
```

Only show this section if real differences are found. Skip it if everything aligns.

---

## Step 3 — Dev handoff

After showing the board, output quick-launch commands for each open story:

```
Quick start:
  /bellosoft-dev-plan PROJ-43   ← plan with AI (TDD approach)
  /bellosoft-dev-plan PROJ-45   ← plan with AI

Or work directly from Jira/Plane — no skill required.
```

If any story is blocked, flag it explicitly:
```
⚠️ PROJ-44 is blocked by PROJ-38. Consider working on PROJ-43 or PROJ-45 first.
```

---

## Step 4 — Offer sync if status looks stale

If local `docs/planning-artifacts/status.md` exists but differs from tracker state:
```
ℹ️ Local plan is out of sync with tracker ([N] differences found).
Run /bellosoft-sync pull to update it.
```

---

## Hard rules
- Never modify tracker state — this skill is read-only
- Always show blocked stories prominently — they need attention
- Always output the quick-start commands — that's the main value of this skill
- If sprint end date is within 2 days and To Do stories remain, flag it:
  `⚠️ Sprint ends in [N] days — [N] stories still To Do. Consider flagging for carry-over.`
