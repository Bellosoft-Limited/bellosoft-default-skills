---
name: bellosoft-plane
description: >
  Central Plane.so integration layer for all bellosoft skills. Handles ALL Plane
  operations — create/update epics, stories, tasks, cycles, comments, and project
  scaffolding. Other bellosoft skills MUST delegate Plane operations here rather
  than calling Plane MCP tools directly. Triggers: /bellosoft-plane, "create plane
  project", "scaffold plane", "push to plane", "update plane ticket", "sync to plane",
  or when any bellosoft skill needs to read/write Plane.
---

# Skill: bellosoft-plane

**This is the Plane service layer for the bellosoft ecosystem.**

All other bellosoft skills delegate Plane operations here. No other skill should
call Plane MCP tools or REST API directly — route through this skill instead.

```
/bellosoft-plane setup           ← first-time project scaffold
/bellosoft-plane create-epic     ← create epic (called by plan-epic)
/bellosoft-plane create-story    ← create story (called by plan-epic, dev-plan)
/bellosoft-plane create-task     ← create task (called by plan-epic, plan-adhoc)
/bellosoft-plane create-cycle    ← create sprint/cycle (called by plan-epic)
/bellosoft-plane update          ← update state/comment (called by sync, dev-review)
/bellosoft-plane get             ← fetch issue by ID (called by dev-plan, sprint)
/bellosoft-plane list-sprint     ← list active sprint (called by bellosoft-sprint)
/bellosoft-plane sync-epics      ← bulk push docs/planning-artifacts/epics.md → Plane
/bellosoft-plane import          ← import existing Plane project → docs/planning-artifacts/
```

---

## Step 0 — Always load first

**At the start of every invocation, load:**
```
references/workflow.md
```

This file contains the battle-tested Plane API quirks table, tool name corrections,
HTML formatting rules, member ID resolution, and state mapping. **Never skip this.**
All Plane operations must follow the rules in that file.

---

## Step 1 — Setup and auth

**Goal: resolve workspace slug, API key, project, and member ID upfront. Never mid-operation.**

### Step 1a — Workspace slug

**Always read the file first. Run this exact command:**

```bash
# On Windows (PowerShell):
if (Test-Path ".secrets/plane-workspace.txt") { Get-Content ".secrets/plane-workspace.txt" -Raw }
# On Mac/Linux (bash):
cat .secrets/plane-workspace.txt 2>/dev/null
```

**Resolution order (stop at first success):**

1. **Read `.secrets/plane-workspace.txt`** — run the command above; if file exists and non-empty, use value silently
2. Check `docs/planning-artifacts/plane-profile.md` — if `workspace_slug` present, save to `.secrets/plane-workspace.txt` and use silently
3. Try MCP: call `mcp_plane_list_projects` — if succeeds, extract slug from project URLs and save to `.secrets/plane-workspace.txt`
4. If all above fail, prompt once:
   `"What is your Plane workspace slug? (visible in the URL: app.plane.so/{slug}/...)"`
   Save to `.secrets/plane-workspace.txt`.

**Never proceed without a workspace slug.** All REST API calls and MCP calls require it.

### Step 1b — API key (resolved during setup)

The API key is required for all write operations MCP cannot handle: creating epics
(`POST /epics/`) and typed work items (`POST /work-items/` with `type_id`).
It is also the fallback for all read operations when MCP is unavailable.

**Always read the file first. Run this exact command:**

```bash
# On Windows (PowerShell):
if (Test-Path ".secrets/plane-api-key.txt") { Get-Content ".secrets/plane-api-key.txt" -Raw }
# On Mac/Linux (bash):
cat .secrets/plane-api-key.txt 2>/dev/null
```

**Resolution order (stop at first success):**

1. **Read `.secrets/plane-api-key.txt`** — run the command above; if file exists and non-empty, use value silently
2. Check `PLANE_API_KEY` env var — if set, use silently
3. If neither found, prompt once:
   `"A Plane API key is needed. Get it from Plane → Profile → Personal Access Tokens:"`
4. Save to `.secrets/plane-api-key.txt` immediately
5. Ensure `.secrets/` is gitignored — append if missing:
   ```bash
   grep -qxF '.secrets/' .gitignore || echo '.secrets/' >> .gitignore
   ```

### Step 1c — MCP connectivity (optional enhancement)

Try `mcp_plane_list_projects` silently. If it succeeds, use MCP tools for reads (faster).
If it fails or is unavailable, fall back to REST API for all operations — **do not stop**.
MCP is a convenience, not a requirement.

### Step 1d — Project resolution

**Resolution order:**

1. Check `docs/planning-artifacts/status.md` for `plane_project_id` and `plane_project_identifier` → use silently
2. If not found, call REST: `GET /api/v1/workspaces/{slug}/projects/` with API key
   - One project → use silently, notify: `"Using project: {name}"`
   - Multiple projects → list and ask which to use
   - No projects → offer: `"No projects found. Type 'create' to scaffold one."` → SETUP

Store `project_id` and `project_identifier` for the session.

### Step 1e — Member ID resolution

1. Check `docs/planning-artifacts/plane-profile.md` — if `plane_member_id` present, use silently
2. Otherwise call REST: `GET /api/v1/workspaces/{slug}/members/` with API key. Match by email or display name.
3. Save result to `docs/planning-artifacts/plane-profile.md`:

```markdown
# Plane Profile
- **display_name**: [name]
- **plane_member_id**: [uuid]
- **workspace_slug**: [slug]
```

**Never defer this to mid-operation.** Interrupting a create/update flow to ask for the
key causes failures and confusion. Resolve it once, upfront, and reuse throughout the session.

---

## Critical API Rules (summary — full details in workflow.md)

These rules are non-negotiable. Violating them causes pydantic validation errors:

| Operation | ❌ Wrong | ✅ Correct |
|-----------|---------|-----------|
| Update state | `state_id=` | `state=` |
| Create/update text | `description=` | `description_html=` |
| Add comment | `data=` | `comment_html=` |
| Search issues | `mcp_plane_search_work_items` | **NEVER USE** — returns empty. Use `mcp_plane_retrieve_work_item_by_identifier` |
| Create epic | `mcp_plane_create_work_item` with Epic type | REST `POST /epics/` endpoint only |
| Create story | `mcp_plane_create_work_item` | REST `POST /work-items/` with `type_id` = User Story type ID |
| Lookup by ID | `mcp_plane_search_work_items` | `mcp_plane_retrieve_work_item_by_identifier(issue_identifier=N, project_identifier="PROJ")` |

**`description_html` format rules:**
- Must be real HTML — compact, single-line, no `\n` between tags
- Wrap content in `<div>`
- Allowed: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<code>`
- Forbidden: `<table>`, `<hr>`, markdown syntax, whitespace/indentation between tags

**Always fetch before transitioning:**
- States: `mcp_plane_list_states(project_id)` → build name→ID map
- Transitions: fetch states first, never hardcode state IDs

---

## Operation: CREATE_EPIC

Called by: `bellosoft-plan-epic` after approval

**Input:**
```
title: string
description: string (plain text — skill converts to description_html)
epic_number: string (e.g. "E1")
```

**Execution:**
```bash
curl -s -X POST \
  "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/{project_id}/epics/" \
  -H "X-API-Key: {key}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Epic {N}: {title}","description_html":"<div><p>{description}</p></div>","labels":["{ai-generated label ID}"]}'
```

Save returned `id` and `sequence_id`.

**Returns:** `{ epic_id, sequence_id, url }`

---

## Operation: CREATE_STORY

Called by: `bellosoft-plan-epic`, `bellosoft-dev-plan` (free-text flow), `bellosoft-plan-adhoc`

**Input:**
```
title: string
user_story: string ("As a ... I want ... so that ...")
acceptance_criteria: string[]
epic_id: string (Plane epic UUID — from CREATE_EPIC)
cycle_id: string (optional — assign to sprint)
estimate_hours: number
priority: "urgent" | "high" | "medium" | "low" | "none"
assignee_id: string (optional)
labels: string[] (optional — e.g. ["backend", "ai-generated"])
```

**Execution:**

First, resolve User Story type ID (see workflow.md Step 6). Then:

```bash
curl -s -X POST \
  "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/" \
  -H "X-API-Key: {key}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{title}",
    "description_html": "<div><p><strong>As a</strong> {persona}, <strong>I want to</strong> {action} <strong>so that</strong> {outcome}.</p><h3>Acceptance Criteria</h3><ul><li>{AC1}</li><li>{AC2}</li></ul></div>",
    "parent": "{epic_id}",
    "state": "{backlog_state_id}",
    "priority": "{priority}",
    "type_id": "{USER_STORY_TYPE_ID}",
    "estimate_point": {estimate_hours},
    "labels": ["{label_ids}"]
  }'
```

If `cycle_id` provided → add to cycle after creation:
```bash
curl -s -X POST \
  "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/{project_id}/cycles/{cycle_id}/cycle-issues/" \
  -H "X-API-Key: {key}" \
  -H "Content-Type: application/json" \
  -d '{"issues": ["{work_item_id}"]}'
```

Add source comment:
```bash
# comment_html: "<p><strong>Source:</strong> docs/planning-artifacts/epics.md — Story {story_id}</p>"
mcp_plane_create_work_item_comment(project_id, work_item_id, comment_html=...)
```

**Returns:** `{ story_id (Plane sequence_id), work_item_id (UUID), url }`

---

## Operation: CREATE_TASK

Called by: `bellosoft-plan-epic` (for sub-tasks), `bellosoft-plan-adhoc`

**Input:**
```
title: string                (task description, without tag prefix)
task_id: string              (e.g. "E1-S1-T1" — epic.story.task numbers)
acceptance_criterion: string
estimate_hours: number
parent_story_id: string      (Plane work item UUID)
area_tag: string             (BE/FE/DB/QA/INFRA/etc.)
depends_on: string[]         (optional — Plane work item IDs)
labels: string[]             (optional)
```

**Task name format:** `{task_id} [{area_tag}] {title}`
- `task_id` = decomposition ID (e.g. `E1-S1-T1`)
- `area_tag` = tag from the `area_tag` parameter (`BE`, `FE`, `DEVOPS`, `QA`)
- `title` = clean description with NO tag prefix
Example: `E8-S2-T1 [BE] Add ScheduleAsync method to CampaignService`

**Execution:**

Resolve Task type ID (default type, `is_default: true`). Then:

```bash
curl -s -X POST \
  "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/" \
  -H "X-API-Key: {key}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{task_id} [{TAG}] {title}",
    "description_html": "<div><h3>Acceptance Criterion</h3><p>{AC}</p><p><strong>Estimate:</strong> {N}h</p></div>",
    "parent": "{parent_story_id}",
    "state": "{backlog_state_id}",
    "type_id": "{TASK_TYPE_ID}",
    "estimate_point": {estimate_hours},
    "labels": ["{label_ids}"]
  }'
```

**Returns:** `{ task_id (sequence_id), work_item_id (UUID), url }`

---

## Operation: CREATE_CYCLE

Called by: `bellosoft-plan-epic` before pushing stories

**Input:**
```
name: string        (e.g. "Sprint 3")
start_date: string  (YYYY-MM-DD)
end_date: string    (YYYY-MM-DD)
```

First check if cycle already exists:
```
mcp_plane_list_cycles(project_id) → filter by name (case-insensitive)
```

If exists → confirm with user before creating a duplicate.
If not → create:
```
mcp_plane_create_cycle(project_id, name, start_date, end_date)
```

**Returns:** `{ cycle_id (UUID) }`

---

## Operation: UPDATE

Called by: `bellosoft-sync` after dev milestones

**Input:**
```
issue_identifier: number   (Plane sequence number, e.g. 42)
action: "transition" | "comment" | "assign"
state_name: string         (for transition — e.g. "In Development", "In Review", "Done")
comment: string            (for comment — plain text, skill converts to comment_html)
assignee_id: string        (for assign)
```

**Execution:**

Fetch issue: `mcp_plane_retrieve_work_item_by_identifier(issue_identifier=N, project_identifier="PROJ")`

For transition:
1. `mcp_plane_list_states(project_id)` → map name → ID
2. `mcp_plane_update_work_item(project_id, work_item_id, state={state_id})`

For comment:
```
mcp_plane_create_work_item_comment(project_id, work_item_id,
  comment_html="<div><p>{comment converted to HTML}</p></div>")
```

**Hard rule:** Never transition to Done without explicit ✅ READY signal from
`bellosoft-dev-review` or explicit user instruction.

---

## Operation: GET

Called by: `bellosoft-dev-plan`, `bellosoft-sprint`

**Input:** `issue_identifier: number`

**Try MCP first:**
```
mcp_plane_retrieve_work_item_by_identifier(
  issue_identifier={N},
  project_identifier="{PROJ}"
)
```

**If MCP unavailable, fall back to REST:**
```bash
curl -s "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/?sequence_id={N}" \
  -H "X-API-Key: {key}"
```
Filter `results` array for the item where `sequence_id == N`.

Note: The `/work-items/{N}/` path (using sequence number directly) does NOT work — Plane requires the UUID. Always list and filter by `sequence_id`.

Extract: title, description_html, acceptance criteria, state, assignee, cycle, labels.

**Returns:** structured story object ready for `bellosoft-dev-plan` to consume.

---

## Operation: LIST_SPRINT

Called by: `bellosoft-sprint`

**Input:** `scope: "mine" | "team"`, `assignee_id: string (optional)`

1. Find active cycle: `mcp_plane_list_cycles(project_id)` → filter `status: "current"`
2. Fetch issues: `mcp_plane_list_cycle_issues(project_id, cycle_id)`
3. Paginate: always use `per_page=100` + `cursor=` until `next_cursor` is null
4. If scope = "mine" → filter by `assignee_id`

Group by state group: `cancelled` (blocked), `started` (in progress), `unstarted` (to do), `completed` (done).

**Returns:** grouped issue list with `sequence_id`, `title`, `state`, `assignee`, `priority`.

---

## Operation: SYNC_EPICS

Called by: `bellosoft-sync` (bulk push mode), or directly

Upsert every epic and story from `docs/planning-artifacts/epics.md` → Plane.
`docs/planning-artifacts/epics.md` is the source of truth — safe to re-run.

**Behavior:**
- Creates epics/stories not yet in Plane
- Updates name/description if changed in epics.md
- Never changes state, assignees, labels, or priority on existing items
- Never deletes

**Steps:**
1. Read `docs/planning-artifacts/epics.md` — extract all epics and stories
2. Print full list and ask: `"Push N epics, N stories to Plane? [y/n]"`
3. Fetch all existing epics (paginate) + work items (paginate) — build name→ID lookup
4. Resolve `ai-generated` label ID (create if missing, color `#7C3AED`)
5. Resolve User Story type ID (see workflow.md)
6. Upsert epics via REST `/epics/` (see CREATE_EPIC — skip if already in sync)
7. Upsert stories via REST `/work-items/` with `type_id` (see CREATE_STORY — skip if already in sync)
8. Update `docs/planning-artifacts/status.md` with Plane sequence IDs

**Name matching rule:** strip `[PROJ-N]` suffix before comparing.
Example: `Epic 1 [BEL-5]: Auth` → compare as `Epic 1: Auth`.

**Summary output:**
```
✅ SYNC_EPICS complete
  Created: N epics, N stories
  Updated: N epics, N stories
  Skipped: N (already in sync)
  Failed:  N — markdown for manual creation below
```

---

## Operation: IMPORT

Called by: `bellosoft-sync import`

Fetch existing Plane project structure → build `docs/planning-artifacts/epics.md` + `docs/planning-artifacts/status.md`.

See `bellosoft-sync` IMPORT mode for full flow — this operation handles the
Plane-side fetching using correct pagination and tool calls.

---

## Operation: SETUP (CREATE_PROJECT)

First-time project scaffold. Creates a Plane project with bellosoft-standard
states, labels, and work item types. See `references/workflow.md` CREATE_PROJECT
section for the full step-by-step — it contains the exact state names, colors,
label list, and work item type definitions.

**ALREADY CONFIGURED CHECK — run this first, before anything else:**
1. Check `docs/planning-artifacts/status.md` for a `project_id:` or `plane_project_id:` line
2. If found → call `mcp_plane_list_projects` to confirm the project still exists
3. If project exists → **stop immediately** and report:
   ```
   ✅ Plane already configured:
     Project: {name} ({identifier})
     Project ID: {project_id}
     Workspace: {workspace_slug}
   No setup needed. To re-scaffold, delete docs/planning-artifacts/status.md first.
   ```
4. Only proceed with phases below if no project is found.

**CRITICAL: Execute in phases. Stop and confirm between each phase. Never run all phases in one shot.**

### Phase 1 — Create project
Follow workflow.md Step 1 (gather inputs) and Step 2 (create project).
- Ask for `project_name` and `identifier`
- Confirm with user before creating
- Never pass `is_time_tracking_enabled` → causes 400
- Handle 409 identifier collisions with `{ID}2`, `{ID}3` retries
- **After project is created: stop and report** `"✅ Project created: {name} ({IDENTIFIER}) — project_id: {id}. Proceed to configure states? [y/n]"`

### Phase 2 — Configure states
Follow workflow.md Step 3 only.
- Fetch existing states, upsert the 9 standard states
- **After states are configured: stop and report** `"✅ States configured (N created, M updated). Proceed to create labels? [y/n]"`

### Phase 3 — Create labels
Follow workflow.md Step 4 only.
- Fetch existing labels, create only missing ones from the 26-label list
- **After labels are created: stop and report** `"✅ Labels done (N created, M skipped). Proceed to create work item types? [y/n]"`

### Phase 4 — Create work item types
Follow workflow.md Step 5 only.
- Use direct curl (not `mcp_plane_list_work_item_types` — it's unreliable)
- Detect existing default Task type, skip creating it
- Create Bug, User Story, Test — all with `is_epic: false`
- **After types are created: stop and report** `"✅ Work item types done (N created, M skipped). Proceed to create custom properties? [y/n]"`

### Phase 5 — Create custom properties
Follow workflow.md Step 6 only.
- For each type, fetch existing properties first, skip if already present
- Create the 10 properties (Deploy Date, Affected Files, Spec Link) across 4 types
- **After properties are created: stop and report full summary** per workflow.md Step 8, then offer to run sync-epics.

Key rules (all phases):
- Identifier must be globally unique — retry with `{ID}2`, `{ID}3` on 409
- Never pass `is_time_tracking_enabled` → causes 400
- Work item types: Task (default), Bug, User Story, Test — all `is_epic: false`
- Icon/color for types must be set manually in Plane UI after scaffold
- If any phase fails, report the error and ask the user how to proceed — never auto-retry more than once

---

## How other bellosoft skills call this skill

Other skills do NOT call Plane MCP tools directly. Instead they describe the
operation needed and this skill executes it. Examples:

**bellosoft-plan-epic** after approval:
```
→ bellosoft-plane: create-cycle "Sprint 3" 2026-06-10 2026-06-24
→ bellosoft-plane: create-epic E1 "User Auth" "Handles login, registration, JWT"
→ bellosoft-plane: create-story E1-S1 ... epic_id=... cycle_id=...
→ bellosoft-plane: create-task E1-S1-T1 "Add users table migration" ... area_tag=BE
```

**bellosoft-sync** after dev-review ✅ READY:
```
→ bellosoft-plane: update NOKEY-42 transition "In Review"
→ bellosoft-plane: update NOKEY-42 comment "Review passed. All ACs covered..."
```

**bellosoft-sprint**:
```
→ bellosoft-plane: list-sprint mine
```

**bellosoft-dev-plan** (free-text flow, user wants ticket):
```
→ bellosoft-plane: create-story ... (no epic, standalone)
```

---

## Error handling

- Log every failure, never silently drop
- Continue after individual failures — collect and report at the end
- For bulk operations (SYNC_EPICS): always produce markdown fallback for failed items
- HTTP 409 on project create = identifier collision → retry automatically
- MCP `Output validation error: None is not of type 'string'` is often a false positive → verify via curl GET before reporting failure

---

## Hard rules
- Always load `references/workflow.md` before any Plane operation
- Never use `mcp_plane_search_work_items` — it returns empty results
- Always use `state=` not `state_id=`
- Always use `comment_html=` not `data=`
- Always create epics via REST `/epics/` — not as work items
- Always create stories via REST `/work-items/` with `type_id` = User Story type ID
- Never hardcode state IDs — always fetch and map by name
- Confirm before any bulk operation > 10 items
- Never delete epics or work items
