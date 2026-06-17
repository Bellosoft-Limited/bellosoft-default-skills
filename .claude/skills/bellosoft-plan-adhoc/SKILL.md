---
name: bellosoft-plan-adhoc
description: >
  Use this skill to add bugs, hotfixes, unplanned tasks, or tech debt to the
  existing sprint plan. Triggers: /bellosoft-plan-adhoc, "log a bug", "add a hotfix",
  "there's an issue in production", "add tech debt", "unplanned work",
  "we found a bug in X", "add a task outside the PRD". Does NOT require a PRD.
  Works independently of /bellosoft-plan-epics and /bellosoft-plan-epic. Optionally pushes to Jira
  or Plane via MCP.
---

# Skill: bellosoft-plan-adhoc

## Purpose
Capture and structure bugs, hotfixes, unplanned feature requests, and tech debt
outside the normal PRD → epic → story flow. Keeps the same format and tag
conventions as the rest of the plan so everything stays consistent.

---

## Invocation

```
/bellosoft-plan-adhoc                        ← interactive, asks for details
/bellosoft-plan-adhoc "login fails on iOS"   ← inline description
/bellosoft-plan-adhoc tech-debt              ← opens tech debt mode
```

---

## Step 1 — Classify the work

Ask (or infer from the description):

```
What type of work is this?

  1. 🐛 Bug         — something broken in production or QA
  2. 🔥 Hotfix      — critical bug, needs immediate fix this sprint
  3. 📋 Unplanned   — valid feature/task not in the PRD (scope addition)
  4. 🔧 Tech debt   — no user-visible change, improves codebase
  5. 🔒 Security    — vulnerability or compliance issue
```

---

## Step 2 — Gather details

For **Bug / Hotfix / Security**:
```
1. Title: [one-line description]
2. Where: [component, page, endpoint, or "unknown"]
3. What happens: [observed behaviour]
4. What should happen: [expected behaviour]
5. Steps to reproduce: [if known]
6. Impact: [who is affected, how many users, data at risk?]
7. Severity: Critical / High / Medium / Low
8. Environment: Production / Staging / QA / Local
```

For **Unplanned / Tech Debt**:
```
1. Title: [one-line description]
2. Why now: [what triggered this — customer request, perf issue, etc.]
3. What needs doing: [description]
4. Impact if deferred: [what happens if we skip this sprint]
5. Priority: High / Medium / Low
```

---

## Step 3 — Decompose into tasks

Apply the same atomicity rules as `/bellosoft-plan-epic`:
- Each task: 2-8h, max 3-5 files, one AC, one area tag
- **Estimates:** Single hours only (2h, 3h, not ranges). Total = sum of all task estimates. When pushed to Jira, each task gets its own timetracking, and parent gets the total.

**QA requirements by work type:**
- **Bugs / Hotfixes:** Always include a `[QA]` sign-off task (mandatory)
- **Unplanned / Tech debt:** Include `[QA]` only if affects user-visible behavior (e.g., UI, API, workflow changes)
- **QA scope:** Manual verification and regression testing only. Test code for fixes goes in `[BE]`/`[FE]` implementation task.

### Bug task template:
```markdown
## 🐛 BUG-[N]: [Title]
**Type:** Bug | **Severity:** [Critical/High/Medium/Low]
**Reported:** [date]
**Environment:** [Production/Staging/QA]
**Epic parent:** [E1 or "Standalone" if no parent epic]

**Observed:** [what is broken]
**Expected:** [what should happen]
**Steps to reproduce:** [if known]

### Root cause hypothesis
[Claude's best guess at root cause from description — or "unknown, needs investigation"]

### Tasks

| ID | Tag | Title | Est | Depends on | Acceptance Criterion |
|----|-----|-------|-----|------------|----------------------|
| BUG-N-T1 | [BE/FE/DB] | Investigate and identify root cause | 2h | — | Root cause documented in ticket |
| BUG-N-T2 | [BE/FE/DB] | Fix: [specific fix description] | 3h | BUG-N-T1 | [Observed behaviour no longer occurs] |
| BUG-N-T3 | [QA] | QA sign-off: verify fix and no regressions | 1h | BUG-N-T2 | QA confirmed: bug is gone, no related breakage |

**Total estimate:** 6h (example; adjust per bug complexity)
**Suggested sprint:** Current sprint (hotfix) / Next sprint / Backlog
```

### Unplanned / Tech debt template:
```markdown
## 📋 UNPL-[N]: [Title]  (or 🔧 DEBT-[N] for tech debt)
**Type:** [Unplanned/Tech debt/Security]
**Priority:** [High/Medium/Low]
**Requested:** [date]
**Epic parent:** [E1 or "Standalone"]

**Description:** [what needs to be done]
**Rationale:** [why this was added outside the PRD]

### Tasks

| ID | Tag | Title | Est | Depends on | Acceptance Criterion |
|----|-----|-------|-----|------------|----------------------|
| UNPL-N-T1 | [TAG] | [Task] | 2h | — | [AC] |
| UNPL-N-T2 | [QA] | QA sign-off: verify UNPL-N | 1h | UNPL-N-T1 | QA confirmed: all ACs pass |

**Total estimate:** 2h (no QA) or 3h (with QA if user-visible)
**Impact if deferred:** [from Step 2]

⚠️ **Include T2 [QA] task only if this affects user-visible behavior (UI, API, workflow).** Omit for internal refactors or invisible improvements.
```

---

## Step 4 — Sprint placement recommendation

```
## Recommended placement

Given the current sprint status:
- **Hotfix / Critical:** Add to current sprint immediately, flag as unplanned
- **High:** Add to current sprint if capacity allows, else top of next sprint
- **Medium:** Add to next sprint backlog
- **Low / Tech debt:** Backlog, review at next sprint planning

Recommendation for this item: [specific suggestion with rationale]

Current sprint capacity used: [read from docs/planning-artifacts/status.md if available]
```

---

## Step 5 — Approval gate

```
---
Reply with:
  ✅ approve              — save + proceed to push options
  ✏️  [feedback]          — adjust tasks or classification
  🔥 hotfix               — mark as critical, push to current sprint now
  ❌ cancel
```

---

## Step 5.5 — Tracker resolution (first-time only)

Before pushing:
- If `docs/planning-artifacts/status.md` contains `tracker:` → skip this step
- If not → load and follow `.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`

---

## Step 6 — Push (optional)

Push to whichever tracker is configured in `docs/planning-artifacts/status.md`:

**Plane** → delegate to `/bellosoft-plane`:
- Bug/Hotfix: `/bellosoft-plane create-story` with Bug type
- Task/Tech debt: `/bellosoft-plane create-task`

**Jira** → delegate to `/bellosoft-jira`:
- Bug/Hotfix: `/bellosoft-jira create-story` with issue_type=Bug, priority=Highest
- Task/Tech debt: `/bellosoft-jira create-task` (standalone, no parent)

**None** → markdown only

For bugs/hotfixes: set issue type to **Bug** and flag high priority.
For hotfixes → assign to current sprint/cycle.

---

## Step 7 — Dev handoff

After push (or markdown-only approval), output the dev handoff block:

```
## 🔧 Ready for development — [BUG-N / UNPL-N]

**Ticket:** [Jira/Plane URL, or "see markdown above"]

This item follows the same dev workflow as any story:

  Option A — with AI assistance:
    /bellosoft-dev-plan [BUG-N or ticket ID]   ← plan the fix with TDD approach
    /bellosoft-dev-execute                        ← implement
    /bellosoft-dev-review                         ← validate and close

  Option B — without AI:
    Work directly from the ticket in Jira/Plane
    The [QA] sign-off task is mandatory regardless of approach — this is manual QA verification, not test code

Note: for hotfixes, the regression test task (BUG-N-T3) should be
completed in the same PR as the fix — never deferred.
```

---

## Step 8 — Update state

Append to `docs/planning-artifacts/status.md` under a separate section:

```markdown
## Bugs & Unplanned Work

| ID | Type | Title | Severity | Sprint | Status | Pushed to |
|----|------|-------|----------|--------|--------|-----------|
| BUG-1 | Bug | [title] | High | Sprint 4 | 🔲 Open | Jira BUG-123 |
| UNPL-1 | Unplanned | [title] | Medium | Sprint 5 | 🔲 Open | — |
```

---

## Hard rules
- **Estimates:** Single hours only (2h, 3h, not ranges). No task over 8h. Total = sum of all task estimates (enforced at Jira push time).
- **QA requirement:** Bugs/hotfixes MUST have `[QA]` task. Unplanned/tech debt have `[QA]` ONLY if user-visible (as defined in Step 3). QA scope is manual verification only — test code goes in `[BE]`/`[FE]` task.
- **Hotfixes:** Go to current sprint — do not defer. QA sign-off must complete in same PR as fix.
- **Classification:** Always explicit (Bug / Hotfix / Unplanned / Debt / Security)
- **Documentation:** Always update docs/planning-artifacts/status.md with Jira IDs after pushing.
- **Dev handoff:** Never skip — devs need to know they can work with or without AI.
