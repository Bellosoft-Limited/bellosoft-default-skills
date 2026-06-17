---
name: bellosoft-plan-epic
description: >
  Use this skill to decompose a single epic into stories and atomic tasks, OR to repair
  an already-pushed epic whose tasks have missing/weak acceptance criteria.
  Triggers: /bellosoft-plan-epic E1, /bellosoft-plan-epic E3, "break down epic 2", "create stories
  for E1", "decompose E3 into tasks", "fix E5 tasks", "re-decompose E5", "E5 tasks are missing ACs",
  "repair epic tasks in Jira". Requires /bellosoft-plan-epics to have been run first
  (reads docs/planning-artifacts/epics.md). Works on ONE epic at a time.
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
/bellosoft-plan-epic E2 redo     ← re-decompose E2 after PRD changes (start from scratch)
/bellosoft-plan-epic E5 fix      ← repair existing tasks (missing ACs, bad estimates, gaps vs PRD)
```

> Use `fix` when the epic is already in the tracker but tasks are incomplete.
> Use `redo` when the PRD changed and you want a completely fresh decomposition.

---

## Step 0.5 — Tracker resolution (first-time only)

Before any push operation, check if tracker is already configured:
- If `docs/planning-artifacts/status.md` contains `tracker:` → skip this step entirely
- If not → load and follow `.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`

This step runs silently when re-running on an already-configured project.

---

## Step 1 — Load state

1. Read `docs/planning-artifacts/epics.md` — get the target epic definition
2. Read `docs/planning-artifacts/status.md` — check current state of that epic
3. Read `docs/planning-artifacts/prd-source.md` — for full context
4. Check `docs/planning-artifacts/codebase-audit.md` — staleness check before using

If `docs/planning-artifacts/epics.md` doesn't exist:
```
No epic register found. Please run /bellosoft-plan-epics first.
```

If the epic is already decomposed (status.md shows stories exist):
```
Epic E[N] already has stories created.
Options:
  /bellosoft-plan-epic E[N] fix     ← repair existing tasks (missing ACs, gaps vs PRD)
  /bellosoft-plan-epic E[N] redo    ← re-decompose from scratch (PRD changed)
  /bellosoft-plan-epic E[N] add     ← add more stories to existing epic
```

**Tracker check** — before decomposing, check whether stories already exist in Jira/Plane:

If `tracker: jira` (from `docs/planning-artifacts/status.md`):
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
If option 1 → import the existing stories into `docs/planning-artifacts/status.md`, skip Steps 3-6, go straight to Step 8.
If option 2 → proceed with decomposition, flagging any story whose title closely matches an existing ticket.

D) **Tracker connected, epic not found in tracker** → note it:
`ℹ️ Epic not yet pushed to tracker — will offer push after decomposition.`

**Audit staleness check** — run before using the audit:

```bash
stat docs/planning-artifacts/codebase-audit.md 2>/dev/null

find . -newer docs/planning-artifacts/codebase-audit.md \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/bin/*' -not -path '*/obj/*' \
  -not -path '*/docs/planning-artifacts/*' \
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

**If `docs/planning-artifacts/codebase-audit.md` exists (preferred):**
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
- [ ] Include **Gherkin test scenarios** (happy path + edge cases) in the task detail block for every `[BE]` and `[FE]` task

### Conventions (MUST follow)

If the audit defined conventions, every task description MUST reference them:
- Task titles use real file/class/method names from the existing codebase
- e.g. NOT "add scheduling to campaign service" but "add `ScheduleAsync(campaignId, runAt)` to `CampaignService.cs`, following `SendAsync` pattern"
- DB tasks reference the actual migration naming convention from the audit
- FE tasks reference the actual store/composable/component patterns in use
- Test tasks reference the actual test project name and existing test patterns

If no audit exists, derive conventions from Step 2 findings.

Each task carries exactly one tag identifying its work domain:

| Tag | Scope |
|-----|-------|
| `[BE]` | Everything backend: API endpoints, controllers, services, business logic, migrations, schema changes, middleware, DI config, .NET startup |
| `[FE]` | Everything frontend: Vue components, views, composables, UI state (Pinia), responsive/mobile, PWA |
| `[DEVOPS]` | Everything infrastructure: Docker, CI/CD, GitHub Actions, Nginx, Dokploy, env vars, secrets |
| `[QA]` | One task per story — manual QA sign-off. NOT for writing tests (tests are written inside `[BE]`/`[FE]` tasks). The QA person verifies the full story end-to-end and marks it done. |

**Test writing rule:** Unit, integration, and E2E tests are always included inside the `[BE]` or `[FE]` task that implements the feature — never as a separate `[QA]` task. The `[QA]` task is for human verification only.

### Gherkin test scenarios

Every `[BE]` and `[FE]` task detail block MUST include Gherkin scenarios that serve as the test specification for the developer implementing it. These define what automated tests must cover:

| Aspect | Requirement |
|--------|-------------|
| **Happy path** | One scenario covering the expected successful flow |
| **Edge cases** | At least one scenario covering a boundary, error, or unusual condition (null, empty, unauthorized, max values, overflow, etc.) |
| **Manual-only flag** | If a scenario is too complex to automate (requires human judgment, visual inspection, or interconnected parts with variable results) but quick to test manually, append `🔶 [manual test only]` to its name. Developers skip writing automated tests and leave these for QA verification. |

Format:
```gherkin
Scenario: [short name] 🔶 [manual test only] (if applicable)
  Given [preconditions]
  When [action]
  Then [expected outcome]
```

Rules:
- Keep each scenario to one `Given`/`When`/`Then` triplet (use `And` for additional conditions)
- Use quoted values for parameters: `Given user "admin" is logged in`
- Scenarios at the task level are more detailed than story ACs — they describe what the test code should assert

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

> **Title rule:** max ~60 characters — short action verb phrase only.
> All implementation specifics (file paths, method names, field lists) go in the **Description**, not the title.

| ID | Tag | Title (short) | Est | Depends on |
|----|-----|---------------|-----|------------|
| E1-S1-T1 | [BE] | [Short action phrase] | 3h | — |
| E1-S1-T2 | [FE] | [Short action phrase] | 3h | E1-S1-T1 |
| E1-S1-T3 | [QA] | QA: test [Story title] | 1h | E1-S1-T2 |

For each task, include a detail block immediately below the table row (in a sub-section when saving to file, or inline when pushing to tracker):

```
E1-S1-T1 [BE]
  Title:       Create Tenant entity
  Description: Create `Tenant.cs` in `Core/Entities/`. Fields: Id (Guid), Name, Slug,
               IsActive, CreatedAt, UpdatedAt. Pure POCO — no EF attributes, no base class.
  AC:          Tenant.cs compiles with no EF/Infrastructure references; all properties public get/set.
  Test Scenarios:
    - Given valid name and slug, when creating a Tenant, then all properties are set correctly
    - Given empty slug, when creating a Tenant, then validation throws
    - Given slug exceeds max length, when creating a Tenant, then validation throws
  Estimate:    3h
  Depends on:  —

E1-S1-T2 [FE]
  Title:       Tenant settings form
  Description: Add settings form component in `src/views/Settings.vue`. Binds to tenant
               store. Uses existing Vuetify form patterns from ContactDetailView.
  AC:          Form saves successfully; validation errors shown inline.
  Test Scenarios:
    - Given valid form data, when user clicks Save, then tenant is updated and success message shown
    - Given empty required field, when user clicks Save, then inline validation error displayed
    - Given Redis connection failure, when user opens form, then tenant data should load from application's own database 🔶 [manual test only]
    - Given network failure, when user clicks Save, then error toast shown and form data preserved
  Estimate:    3h
  Depends on:  E1-S1-T1

E1-S1-T3 [QA]
  Title:       QA: test tenant settings story
  Description: Manually verify all ACs for story E1-S1 end-to-end on staging.
  AC:          QA confirmed: all story ACs pass, no regressions in related flows.
  Estimate:    1h
  Depends on:  E1-S1-T2
```

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
| [DEVOPS] | N | Xh |
| [QA] | N (1 per story) | Xh |
| **Total** | **N** | **Xh** |

## Dependency graph (critical path)
E1-S1-T1 [BE] → E1-S1-T2 [FE] → E1-S1-T3 [QA]
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
   /bellosoft-plane create-task [task_id] "[title]" "[AC]"
     parent_story_id=[story_work_item_id] estimate=[Xh] area_tag=[TAG]
   (task_id = e.g. E1-S1-T1; title = clean description WITHOUT the tag; area_tag = BE|FE|DEVOPS|QA)
   bellosoft-plane assembles the full name as: {task_id} [{area_tag}] {title}
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
   ⚠️ estimate=[Xh] must equal the sum of all subtask estimates. This sets the story's originalEstimate in Jira.
   → returns story_key (e.g. PROJ-12)

4. For each Task under that Story:
   /bellosoft-jira create-task [task_id] "[title]" "[AC]"
     parent_story_key=[story_key] estimate=[Xh] area_tag=[TAG]
   (task_id = e.g. E1-S1-T1; title = clean description WITHOUT the tag; area_tag = BE|FE|DEVOPS|QA)
   bellosoft-jira assembles the Jira summary as: {task_id} [{area_tag}] {title}
   Each task's estimate=[Xh] sets its own originalEstimate in Jira.
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

After push (or approval if markdown-only), update `docs/planning-artifacts/status.md`:

```markdown
| E1: [name] | ✅ Decomposed | 4 stories, 18 tasks | Jira (2026-06-02) |
```

Output:
```
✅ Epic E[N] done. docs/planning-artifacts/status.md updated.

Other epics not yet decomposed:
  /bellosoft-plan-epic E2    ← do this now or next week
  /bellosoft-plan-epic E3    ← do this when E2 is delivered

To add bugs or unplanned work: /bellosoft-plan-adhoc
To re-read the PRD after changes: /bellosoft-plan-epics
```

---

---

## Operation: FIX (repair existing tracker tasks)

Triggered by: `/bellosoft-plan-epic E[N] fix`

Use when the epic is already in the tracker but tasks have weak or missing acceptance
criteria, wrong estimates, or are missing coverage for PRD requirements.

### Step F1 — Read tracker state

Read `docs/planning-artifacts/status.md` to find all Jira/Plane keys for this epic:
```bash
grep "jira_epic_E5\|jira_story_5\." docs/planning-artifacts/status.md
```
Then delegate to `bellosoft-jira get [EPIC-KEY]` to fetch all sub-tasks with their
current summaries and descriptions.

### Step F2 — Load PRD requirements for this epic

Read `docs/planning-artifacts/prd.md`. Find the Functional Requirements section that
maps to Epic E[N] (use the coverage map in `docs/planning-artifacts/epics.md`).
List the FRs this epic covers — these are the ground truth.

### Step F3 — Load codebase audit module section

Read `docs/planning-artifacts/codebase-audit.md`. Find the module entries for this
epic's feature area. Note: what is already implemented, what is stubbed, what is missing.

### Step F4 — Gap analysis

Compare existing sub-tasks against the PRD FRs:

```
Gap Analysis — Epic E[N]

  Existing sub-tasks: N
  PRD FRs covered by this epic: N

  ✅ Good tasks (has AC, correct estimate):
    [PROJ-XX] E[N]-S1-T1 [FE] ...

  ⚠️  Weak tasks (missing or vague AC):
    [PROJ-XX] E[N]-S2-T1 [BE] ... — no acceptance criterion
    [PROJ-XX] E[N]-S2-T2 [FE] ... — description is a plain string, not ADF

  ❌ Uncovered FRs (no task exists):
    FR-42: ...
    FR-43: ...

  🔀 Tasks to split (>8h or covering multiple FRs):
    [PROJ-XX] E[N]-S3-T1 — covers FR-10 and FR-11, should be two tasks
```

### Step F5 — Produce repair plan

Show a full repair plan:
- For each weak task: proposed new summary + AC + estimate
- For each missing FR: proposed new task with summary, AC, area tag, estimate, parent story
- For each task to split: two replacement tasks

Present the plan for approval exactly like Step 6 (approval gate) in the main flow.

### Step F6 — Apply after approval

For each **existing task** that needs updating:
```
→ bellosoft-jira update [PROJ-XX] description={new ADF} summary={new summary}
```

For each **new task**:
```
→ bellosoft-jira create-task ... parent_story_key=[PROJ-YY]
```

Update `docs/planning-artifacts/status.md` with any new task keys.

Report:
```
✅ FIX complete — Epic E[N]
  Updated: N tasks
  Created: N new tasks
  Unchanged: N tasks (already good)
```

---

## Save path for decomposition plans

Always save the approved decomposition to:
```
docs/planning-artifacts/epic-plans/E{N}-plan.md
```
Create the `epic-plans/` directory if it doesn't exist. Never save to a project-specific name
like `epic-E4-redecomposition.md` — use the standard path so other skills can find it.

---

## Hard rules
- Never decompose more than one epic per invocation
- Never push without approval
- Always update docs/planning-artifacts/status.md
- No task over 8h — split without exception
- Every task has exactly one AC
- Every task has exactly one area tag (two only if inseparable)
- `fix` mode never deletes existing tasks — only updates or adds
