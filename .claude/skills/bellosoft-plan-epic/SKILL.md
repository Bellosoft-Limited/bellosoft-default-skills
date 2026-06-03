---
name: bellosoft-plan-epic
description: >
  Use this skill to decompose a single epic into stories and atomic tasks.
  Triggers: /bellosoft-plan-epic E1, /bellosoft-plan-epic E3, "break down epic 2", "create stories
  for E1", "decompose E3 into tasks". Requires /bellosoft-plan-epics to have been run first
  (reads docs/plan/epics.md). Works on ONE epic at a time — you choose which, and when.
  After approval, optionally pushes to Jira or Plane via MCP. Can be re-run on the
  same epic if requirements changed.
---

# Skill: plan-epic

## Purpose
Take one approved epic from the register and decompose it into stories and atomic
tasks — with area tags, hour estimates, acceptance criteria, and dependencies.
You decide which epic to decompose and when.

---

## Invocation

```
/bellosoft-plan-epic E1          ← decompose epic E1
/bellosoft-plan-epic E3          ← decompose epic E3 (later, different week)
/bellosoft-plan-epic E2 redo     ← re-decompose E2 after PRD changes
```

---

## Step 0.5 — Tracker resolution (first-time only)

Before any push operation, check if tracker is already configured:
- If `docs/plan/status.md` contains `tracker:` → skip this step entirely
- If not → load and follow `.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`

This step runs silently when re-running on an already-configured project.

---

## Step 1 — Load state

1. Read `docs/plan/epics.md` — get the target epic definition
2. Read `docs/plan/status.md` — check current state of that epic
3. Read `docs/plan/prd-source.md` — for full context
4. Check `docs/plan/codebase-audit.md` — staleness check before using

If `docs/plan/epics.md` doesn't exist:
```
No epic register found. Please run /bellosoft-plan-epics first.
```

If the epic is already decomposed (status.md shows stories exist):
```
Epic E[N] already has stories created.
Options:
  /bellosoft-plan-epic E[N] redo    ← re-decompose from scratch (PRD changed)
  /bellosoft-plan-epic E[N] add     ← add more stories to existing epic
```

**Tracker check** — before decomposing, check whether stories already exist in Jira/Plane:

If `tracker: jira` (from `docs/plan/status.md`):
```
# Delegate to bellosoft-jira:
/bellosoft-jira get [EPIC-KEY]  ← then search stories linked to it
```
If `tracker: plane`:
```
# Delegate to bellosoft-plane:
/bellosoft-plane list-stories epic_id=[epicId]
```

**Four outcomes:**

A) **No tracker connected** → proceed with local decomposition, push will be offered at the end.

B) **Tracker connected, no existing stories found** → proceed with full decomposition.

C) **Tracker connected, stories exist** → show them and ask:
```
Found N existing stories for this epic in [Jira/Plane]:
  PROJ-42 — [title] — [state]
  PROJ-43 — [title] — [state]
  PROJ-44 — [title] — [state]

Options:
  1. Import these — skip decomposition, pull stories into local plan (recommended)
  2. Decompose anyway — I'll skip stories that match existing ones by title
  3. Start fresh — ignore tracker stories, re-decompose from PRD (will create duplicates if pushed)
```
If option 1 → import the existing stories into `docs/plan/status.md`, skip Steps 3-6, go straight to Step 8.
If option 2 → proceed with decomposition, flagging any story whose title closely matches an existing ticket.

D) **Tracker connected, epic not found in tracker** → note it:
`ℹ️ Epic not yet pushed to tracker — will offer push after decomposition.`

**Audit staleness check** — run before using the audit:

```bash
stat docs/plan/codebase-audit.md 2>/dev/null

find . -newer docs/plan/codebase-audit.md \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/bin/*' -not -path '*/obj/*' \
  -not -path '*/docs/plan/*' \
  -name "*.cs" -o -name "*.ts" -o -name "*.vue" \
  2>/dev/null | wc -l
```

- **No audit + this epic is 🔶 Continue or 🔁 Rework** (per epics.md):
  ```
  ⚠️ This epic involves existing code but no audit exists.
  I'll do a targeted read of the relevant modules now.
  ```
  → proceed to Step 2 targeted read.

- **Audit stale (> 14 days or > 20 files changed) + epic is 🔶/🔁**:
  ```
  ⚠️ Audit is N days old with N files changed since.
  For a 🔶 Continue epic this matters — I may plan tasks
  for things already finished.

  Options:
    1. Re-run /bellosoft-audit-codebase first
    2. Use stale audit + I'll do a targeted re-read of this epic's files
    3. Use stale audit as-is

  Which would you prefer?
  ```
  If option 2 → load audit for conventions, but re-read the specific
  files for this epic to verify current implementation status.

- **Audit fresh OR epic is 🆕 Greenfield** → load silently, proceed.

**After loading**, note the epic's starting point:
- 🆕 Greenfield → plan all stories from scratch
- 🔶 Continue → first story covers completing existing partial work before new functionality
- 🔁 Rework → first story is a tech debt / rework story
- If audit shows a module as ✅ Complete but epic includes it → skip those stories, note as already done

---

## Step 2 — Load existing implementation context

**If `docs/plan/codebase-audit.md` exists (preferred):**
Read the relevant sections for this epic — Module Inventory, Conventions, Tech Debt.
Do NOT re-read the entire codebase — the audit already captured it.

Use the audit to:
- Identify files that already exist and must be extended (not recreated)
- Identify the exact patterns new tasks must follow (naming, DI, response format, etc.)
- Identify tech debt items that should become tasks in this epic if they block it
- Skip writing tasks for anything already marked ✅ Complete

**If no audit exists:**
Do a targeted read of the relevant modules for this epic only:
- Find existing files/modules this epic will touch (use `Glob`, `Grep`, `Read`)
- Identify the testing framework (xUnit, Vitest, etc.) and test file naming pattern
- Note existing similar implementations to use as patterns
- Check for TODOs or stubs in relevant files

After reading, note what was found:
```
📂 Existing code found for this epic:
- `src/Services/CampaignService.cs` — Create/List implemented, Schedule method is a stub
- `src/Controllers/CampaignController.cs` — 3 endpoints working, 2 return empty Ok()
- `migrations/20251101_AddCampaigns.cs` — table exists, missing ScheduledAt column
- No tests found for campaign module

New work will extend these files, not replace them.
```

---

## Step 3 — Open questions (epic-specific)

Raise ambiguities specific to THIS epic before decomposing:

```
## ❓ Open Questions — Epic E[N]: [Name]

1. [Question about a specific requirement in this epic]
2. [Question about integration or edge case]

Answer or "skip" to proceed with assumptions.
```

---

## Step 4 — Decompose into stories and tasks

### Hierarchy
```
Epic (from register)
└── Story (vertical slice of user value — 3-10 days)
    └── Task (atomic unit of work — 2-8 hours)
```

### Story rules
- Delivers **observable value** to a user or system (not just "implement backend")
- Has 2-5 acceptance criteria in Given/When/Then
- Estimate: sum of its tasks
- Priority: High / Medium / Low

### Task atomicity rules — a task MUST:
- [ ] Have **exactly one area tag** (two only if genuinely inseparable)
- [ ] Touch **max 3-5 files**
- [ ] Be completable in **2-8 hours** — above 8h → split, no exceptions
- [ ] Have **exactly one acceptance criterion** (pass/fail, no ambiguity)
- [ ] Be **independently committable** or have explicit `Depends on` declared
- [ ] Be something a developer can pick up without asking questions

### Conventions (MUST follow)

If the audit defined conventions, every task description MUST reference them:
- Task titles use real file/class/method names from the existing codebase
- e.g. NOT "add scheduling to campaign service" but "add `ScheduleAsync(campaignId, runAt)` to `CampaignService.cs`, following `SendAsync` pattern"
- DB tasks reference the actual migration naming convention from the audit
- FE tasks reference the actual store/composable/component patterns in use
- Test tasks reference the actual test project name and existing test patterns

If no audit exists, derive conventions from Step 2 findings.
| `[BE]` | API endpoints, business logic, services, controllers |
| `[FE]` | Vue components, pages, composables, UI state |
| `[FW]` | .NET config, middleware, DI, program.cs, startup |
| `[DB]` | Migrations, schema, seed data, pgvector, indexes |
| `[INFRA]` | Docker, Dokploy, Hetzner, Proxmox, Nginx, WireGuard |
| `[QA]` | Unit tests, integration tests, E2E, test fixtures |
| `[DEVOPS]` | CI/CD, GitHub Actions, environment vars, secrets |
| `[MOB]` | Mobile UI, PWA, push notifications |

### Estimation guide

| Hours | What it means |
|-------|--------------|
| 1-2h | Config, simple CRUD, single small component |
| 2-4h | Medium endpoint + validation, component with state, migration |
| 4-6h | Complex service, multi-step form, external API integration |
| 6-8h | Large feature slice, auth flow, complex query, data pipeline |
| >8h | ⚠️ Must be split |

---

## Step 5 — Output the decomposition

```markdown
# Epic E[N]: [Epic Name] — Story & Task Breakdown
**Epic goal:** [from register]
**Decomposed:** [today's date]
**Total estimate:** Xh | **Stories:** N | **Tasks:** N

---

## Assumptions
- [Any assumption made]

---

### Story [E1-S1]: [Story title — verb phrase from user perspective]
**As a** [persona], **I want** [action] **so that** [outcome].
**Estimate:** Xh | **Priority:** High
**Acceptance Criteria:**
- Given [context], when [action], then [result]
- Given [context], when [action], then [result]

#### Tasks

| ID | Tag | Title | Est | Depends on | Acceptance Criterion |
|----|-----|-------|-----|------------|----------------------|
| E1-S1-T1 | [DB] | [Specific, concrete title] | 2h | — | [One verifiable criterion] |
| E1-S1-T2 | [BE] | [Specific, concrete title] | 3h | E1-S1-T1 | [One verifiable criterion] |
| E1-S1-T3 | [FE] | [Specific, concrete title] | 3h | E1-S1-T2 | [One verifiable criterion] |
| E1-S1-T4 | [QA] | [Specific, concrete title] | 2h | E1-S1-T3 | [One verifiable criterion] |

---

### Story [E1-S2]: [Story title]
[... repeat ...]

---

## Sprint allocation for this epic

| Sprint | Stories | Estimate | Notes |
|--------|---------|----------|-------|
| Sprint N | E1-S1, E1-S2 | Xh | [rationale] |
| Sprint N+1 | E1-S3 | Xh | [rationale] |

## Tag summary for this epic

| Tag | Tasks | Hours |
|-----|-------|-------|
| [BE] | N | Xh |
| [FE] | N | Xh |
| [DB] | N | Xh |
| [QA] | N | Xh |
| **Total** | **N** | **Xh** |

## Dependency graph (critical path)
E1-S1-T1 [DB] → E1-S1-T2 [BE] → E1-S1-T3 [FE] → E1-S1-T4 [QA]
[...]

## Risk register
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk] | Med | High | [Mitigation] |
```

---

## Step 6 — Approval gate

```
---
E[N] decomposed: N stories, N tasks, ~Xh.

Reply with:
  ✅ approve             — save + proceed to push options
  ✏️  [feedback]         — adjust stories or tasks
  🔀 re-estimate         — redo estimates only
  ➕ add story: [desc]   — add a missing story
  ❌ cancel
```

---

## Step 7 — Push (optional)

After approval, ask:
```
Where would you like to push E[N]?
  1. Plane   (via /bellosoft-plane)
  2. Jira
  3. Markdown only — I'll create tickets manually
```

### Option 1 — Plane

Delegate ALL Plane operations to `/bellosoft-plane` in strict order.
Do NOT call Plane MCP tools directly — bellosoft-plane handles all API quirks,
HTML formatting, type resolution, and error handling.

```
1. /bellosoft-plane create-cycle "[Sprint name]" [start_date] [end_date]
   → returns cycle_id

2. /bellosoft-plane create-epic [E_number] "[title]" "[description]"
   → returns epic_id

3. For each Story:
   /bellosoft-plane create-story [story_id] "[title]" [user_story] [ACs...]
     epic_id=[epic_id] cycle_id=[cycle_id] estimate=[Xh] priority=[high|medium|low]
   → returns story_work_item_id

4. For each Task under that Story:
   /bellosoft-plane create-task "[TAG] [title]" "[AC]"
     parent_story_id=[story_work_item_id] estimate=[Xh] area_tag=[TAG]
```

### Option 2 — Jira

Delegate ALL Jira operations to `/bellosoft-jira` in strict order.
Do NOT call Atlassian MCP tools directly — bellosoft-jira handles ADF format,
custom field discovery, project type detection, and error handling.

```
1. /bellosoft-jira create-sprint "[Sprint name]" [start_date] [end_date]
   → returns sprint_id

2. /bellosoft-jira create-epic [E_number] "[title]" "[description]"
   → returns epic_key (e.g. PROJ-5)

3. For each Story:
   /bellosoft-jira create-story [story_id] "[title]" [user_story] [ACs...]
     epic_key=[epic_key] sprint_id=[sprint_id] estimate=[Xh] priority=[High|Medium|Low]
   → returns story_key (e.g. PROJ-12)

4. For each Task under that Story:
   /bellosoft-jira create-task "[TAG] [title]" "[AC]"
     parent_story_key=[story_key] estimate=[Xh] area_tag=[TAG]
```

### Error handling (all options)
- Log every failure, continue with remaining items
- Never silently drop items
- End with recovery report:
  ```
  ✅ Created: N items
  ❌ Failed: N — markdown for manual creation:
  [markdown for failed items]
  ```


---

## Step 8 — Update state

After push (or approval if markdown-only), update `docs/plan/status.md`:

```markdown
| E1: [name] | ✅ Decomposed | 4 stories, 18 tasks | Jira (2026-06-02) |
```

Output:
```
✅ Epic E[N] done. docs/plan/status.md updated.

Other epics not yet decomposed:
  /bellosoft-plan-epic E2    ← do this now or next week
  /bellosoft-plan-epic E3    ← do this when E2 is delivered

To add bugs or unplanned work: /bellosoft-plan-adhoc
To re-read the PRD after changes: /bellosoft-plan-epics
```

---

## Hard rules
- Never decompose more than one epic per invocation
- Never push without approval
- Always update docs/plan/status.md
- No task over 8h — split without exception
- Every task has exactly one AC
- Every task has exactly one area tag (two only if inseparable)
