---
name: bellosoft-openproject
description: >
  Central OpenProject integration layer for all bellosoft skills. Handles ALL
  OpenProject operations — create/update epics, stories, tasks, versions (sprints),
  comments, and project scaffolding. Other bellosoft skills MUST delegate OpenProject
  operations here rather than calling the API directly. Triggers: /bellosoft-openproject,
  "create openproject epic", "push to openproject", "update openproject ticket",
  "sync to openproject", or when any bellosoft skill needs to read/write OpenProject.
---

# Skill: bellosoft-openproject

**This is the OpenProject service layer for the bellosoft ecosystem.**

All other bellosoft skills delegate OpenProject operations here. No other skill should
call the OpenProject API directly — route through this skill instead.

```
/bellosoft-openproject setup           ← first-time project scaffold
/bellosoft-openproject create-epic     ← create epic (called by plan-epic)
/bellosoft-openproject create-story    ← create story (called by plan-epic, dev-plan)
/bellosoft-openproject create-task     ← create task (called by plan-epic, plan-adhoc)
/bellosoft-openproject create-sprint   ← create version/sprint (called by plan-epic)
/bellosoft-openproject update          ← update state/comment (called by sync, dev-review)
/bellosoft-openproject get             ← fetch work package by ID (called by dev-plan, sprint)
/bellosoft-openproject list-sprint     ← list active version (called by bellosoft-sprint)
/bellosoft-openproject sync-epics      ← bulk push docs/planning-artifacts/epics.md → OpenProject
/bellosoft-openproject import          ← import existing project → docs/planning-artifacts/
```

---

## Step 0 — Always load first

**At the start of every invocation, load:**
```
references/api-guide.md
```

This file contains the OpenProject API patterns, HAL+JSON quirks, filter syntax,
lockVersion rules, and field mappings. **Never skip this.**

---

## Step 1 — Setup and auth

**Goal: resolve all credentials and identifiers upfront. Never ask mid-operation.**

### Step 1a — Credentials

OpenProject REST API requires `OP_URL` and `OP_API_TOKEN` for all requests.

> ⚠️ **Use direct file reads, not glob search.** Run the `cat`/`Get-Content` commands below.
> Do NOT use file-search or glob tools (e.g. searching `**/.secrets/**`) — that pattern does
> not match files directly inside `.secrets/` and will return no results.

**1. Individual secret files:**
```bash
# Mac/Linux (bash):
cat .secrets/op-url.txt 2>/dev/null | tr -d '\n'
cat .secrets/op-api-token.txt 2>/dev/null | tr -d '\n'
# Windows (PowerShell):
if (Test-Path ".secrets/op-url.txt")       { (Get-Content ".secrets/op-url.txt" -Raw).Trim() }
if (Test-Path ".secrets/op-api-token.txt") { (Get-Content ".secrets/op-api-token.txt" -Raw).Trim() }
```

**2. Combined credentials file** — check `.secrets/op-credentials.txt`:
```bash
cat .secrets/op-credentials.txt 2>/dev/null
cat .secrets/openproject.txt 2>/dev/null
```
Parse whatever format is present — look for URL and token/key values.

**3. Env vars** — `OP_URL`, `OP_API_TOKEN`

**4. Only if a value is still missing** — prompt once:
   - URL: `"What is your OpenProject URL? (e.g. https://myorg.openproject.com)"`
   - Token: `"What is your OpenProject API token? (My Account → Access Tokens → Add token)"`

**5. After obtaining any missing value** — save to `.secrets/op-{url,api-token}.txt` and ensure `.secrets/` is gitignored:
```bash
grep -qxF '.secrets/' .gitignore || echo '.secrets/' >> .gitignore
```

All subsequent API calls use:
```bash
OP_URL=$(cat .secrets/op-url.txt | tr -d '\n')
OP_TOKEN=$(cat .secrets/op-api-token.txt | tr -d '\n')
# Then: -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json"
```

### Step 1b — User identity

1. Read `.secrets/op-identity.txt` — if `user_id` line present, use silently.
2. Otherwise fetch:
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/users/me" > /tmp/op_me.json
cat /tmp/op_me.json
```
3. Extract: `id`, `name`, `login`, `email`
4. Save to `.secrets/op-identity.txt`:
```
user_id={id}
display_name={name}
login={login}
email={email}
```

### Step 1c — Project resolution

1. Check `docs/planning-artifacts/status.md` for `op_project_id:` — use silently if found
2. If not found → list projects:
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects" > /tmp/op_projects.json
cat /tmp/op_projects.json
```
   - One project → use silently, notify: `"Using project: {name} (id: {id})"`
   - Multiple → list and ask which to use
   - None → offer: `"No projects found. Type 'create' to scaffold one."` → CREATE_PROJECT
3. Store in `docs/planning-artifacts/status.md`:
```
tracker: openproject
op_project_id: {id}
op_project_identifier: {identifier}
```

### Step 1d — Type and status resolution

Types and status IDs differ between OpenProject instances. Always resolve at setup.

**Types:**
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/types" > /tmp/op_types.json
cat /tmp/op_types.json
```
Map to IDs and save to `docs/planning-artifacts/openproject-profile.md`:
- `epic_type_id` — type named "Epic" (case-insensitive). If missing, use Story hierarchy.
- `story_type_id` — type named "Story" or "User Story"
- `task_type_id` — type named "Task" (usually default)
- `bug_type_id` — type named "Bug"

**Statuses:**
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/statuses" > /tmp/op_statuses.json
cat /tmp/op_statuses.json
```
Map to IDs and save:
- `status_new_id` — "New" or "To Do" or the `isDefault: true` status
- `status_in_progress_id` — "In Progress" or equivalent
- `status_in_review_id` — "In Review" or "Code Review" (may not exist)
- `status_done_id` — "Closed" or "Done" (`isClosed: true`)

---

## Critical API Rules

These rules are non-negotiable. Violating them causes API errors:

| Concern | ❌ Wrong | ✅ Correct |
|---------|---------|-----------|
| PATCH without lock | send body only | include `lockVersion` from prior GET |
| Set status | `"status": "In Progress"` | `"_links": {"status": {"href": "/api/v3/statuses/3"}}` |
| Set type | `"type": "Task"` | `"_links": {"type": {"href": "/api/v3/types/1"}}` |
| Set assignee | `"assignee": "John"` | `"_links": {"assignee": {"href": "/api/v3/users/33"}}` |
| Set version | `"version": 42` | `"_links": {"version": {"href": "/api/v3/versions/42"}}` |
| Set parent | `"parentId": 100` | `"_links": {"parent": {"href": "/api/v3/work_packages/100"}}` |
| Hardcode type ID | any integer | fetch from project types endpoint, save to profile |
| Hardcode status ID | any integer | fetch from statuses endpoint, save to profile |

**Always write to temp file, never pipe to jq:**
```bash
curl -s ... > /tmp/op_result.json
cat /tmp/op_result.json
```
Read the raw JSON yourself. Do NOT use `jq`, `python3`, or any external parser.

---

## Operation: SETUP (CREATE_PROJECT)

Runs automatically on first use (triggered by Step 1 above). Discovers and caches
everything needed so subsequent operations never need to ask questions.

**ALREADY CONFIGURED CHECK — run this first:**
1. Check `docs/planning-artifacts/openproject-profile.md` for `project_id` and `type_ids`
2. If complete → **stop immediately** and report:
   ```
   ✅ OpenProject already configured:
     Project: {project_name} (id: {id})
     Types: Epic ({id}), Story ({id}), Task ({id})
     User: {display_name}
   No setup needed. To refresh, delete docs/planning-artifacts/openproject-profile.md first.
   ```
3. Only proceed with discovery below if profile is missing or incomplete.

**Discovery steps (only if not already configured):**
1. Credentials + identity + project already resolved in Step 1 — reuse
2. Fetch types (Step 1d) — resolve and save all type IDs
3. Fetch statuses (Step 1d) — resolve and save all status IDs
4. Fetch project default version/sprint if any

**Profile output — two separate files:**

`docs/planning-artifacts/openproject-profile.md` — project config only (safe to commit):
```markdown
# OpenProject Profile
- **op_url**: https://myorg.openproject.com
- **project_id**: 5
- **project_identifier**: my-project
- **project_name**: My Project
- **type_ids**:
  - epic: 6
  - story: 2
  - task: 1
  - bug: 4
- **status_ids**:
  - new: 1
  - in_progress: 7
  - in_review: 8
  - done: 12
```

`.secrets/op-identity.txt` — personal identity only (gitignored, never committed):
```
user_id={id}
display_name={name}
login={login}
email={email}
```

---

## Operation: CREATE_PROJECT

Called when user has no OpenProject project and wants to scaffold one.

**Input:**
```
project_name: string     (e.g. "My App")
identifier: string       (e.g. "my-app" — lowercase, hyphens, globally unique)
```

**Suggest identifier** from project name (lowercase, spaces → hyphens). User confirms.

**Create:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects" \
  -d '{
    "name": "'"$PROJECT_NAME"'",
    "identifier": "'"$IDENTIFIER"'",
    "description": {"format": "markdown", "raw": ""},
    "public": false
  }' > /tmp/op_new_project.json
cat /tmp/op_new_project.json
```

On 422 (identifier taken) → retry with `{identifier}-2`, `{identifier}-3`.

After creation, run SETUP automatically.

---

## Operation: CREATE_EPIC

Called by: `bellosoft-plan-epic` after approval

**Input:**
```
title: string
description: string (plain text — skill wraps in markdown)
epic_number: string (e.g. "E1")
```

**Execution:**

Load `docs/planning-artifacts/openproject-profile.md` for `project_id` and `epic_type_id`.

If no `epic_type_id` (instance doesn't have Epic type), use `story_type_id` and set
a `[EPIC]` prefix in the subject — note in output that epic is a top-level story.

```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  -d '{
    "subject": "Epic '"$N"': '"$TITLE"'",
    "description": {
      "format": "markdown",
      "raw": "'"$DESCRIPTION"'\n\n_Source: docs/planning-artifacts/epics.md — Epic '"$EPIC_NUMBER"'_"
    },
    "_links": {
      "type":   {"href": "/api/v3/types/'"$EPIC_TYPE_ID"'"},
      "status": {"href": "/api/v3/statuses/'"$STATUS_NEW_ID"'"}
    }
  }' > /tmp/op_new_epic.json
cat /tmp/op_new_epic.json
```

**Returns:** `{ id, subject, self_href }` — save `id` as the epic's work package ID.

---

## Operation: CREATE_STORY

Called by: `bellosoft-plan-epic`, `bellosoft-dev-plan` (free-text flow), `bellosoft-plan-adhoc`

**Input:**
```
title: string
user_story: string ("As a ... I want ... so that ...")
acceptance_criteria: string[]
epic_id: number          (work package ID of the parent epic)
version_id: number       (optional — assign to sprint)
estimate_hours: number
priority: "immediate" | "urgent" | "high" | "medium" | "low" | "lowest"
assignee_id: number      (optional — user ID)
```

OpenProject priority values: `"immediate"`, `"urgent"`, `"high"`, `"medium"`, `"low"`, `"lowest"`.
Map from bellosoft priorities: Highest→immediate, High→high, Medium→medium, Low→low.

**Build description (markdown):**
```markdown
**As a** {persona}, **I want to** {action} **so that** {outcome}.

### Acceptance Criteria
1. {AC1}
2. {AC2}
...
```

**Execution:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  -d '{
    "subject": "'"$TITLE"'",
    "description": {"format": "markdown", "raw": "'"$DESCRIPTION"'"},
    "estimatedTime": "PT'"$HOURS"'H",
    "_links": {
      "type":     {"href": "/api/v3/types/'"$STORY_TYPE_ID"'"},
      "status":   {"href": "/api/v3/statuses/'"$STATUS_NEW_ID"'"},
      "priority": {"href": "/api/v3/priorities/'"$PRIORITY_HREF"'"},
      "parent":   {"href": "/api/v3/work_packages/'"$EPIC_ID"'"},
      "version":  {"href": "/api/v3/versions/'"$VERSION_ID"'"},
      "assignee": {"href": "/api/v3/users/'"$ASSIGNEE_ID"'"}
    }
  }' > /tmp/op_new_story.json
cat /tmp/op_new_story.json
```

Omit optional link objects (`version`, `assignee`) if not provided.

Add source comment after creation:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/$WP_ID/activities" \
  -d '{"comment": {"raw": "Created by bellosoft-plan-epic from docs/planning-artifacts/epics.md"}}'
```

**Returns:** `{ id, subject, url }`

---

## Operation: CREATE_TASK

Called by: `bellosoft-plan-epic` (sub-tasks), `bellosoft-plan-adhoc`

**Input:**
```
title: string                (short action phrase, max ~60 chars — NO implementation details)
implementation_notes: string (file paths, method names, patterns — goes in description)
task_id: string              (e.g. "E1-S1-T1" — epic.story.task numbers)
acceptance_criterion: string
estimate_hours: number
parent_story_id: number      (work package ID of the parent story)
area_tag: string             (BE | FE | DEVOPS | QA)
```

**Subject format:** `{task_id} [{area_tag}] {title}`
Example: `E8-S2-T1 [BE] Add campaign scheduling method`

| ❌ Too long | ✅ Correct |
|---|---|
| `Create Tenant.cs POCO in Core/Entities/Tenant.cs with fields: Id, Name, Slug...` | `Create Tenant entity` |
| `Add ScheduleAsync(campaignId, runAt) method to CampaignService.cs` | `Add campaign scheduling method` |

**Build description:**
```markdown
## Description
{implementation_notes}

## Acceptance Criterion
{acceptance_criterion}

**Estimate:** {estimate_hours}h
```
(Omit Description section if `implementation_notes` is empty.)

**Execution:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  -d '{
    "subject": "'"$TASK_ID"' ['"$AREA_TAG"'] '"$TITLE"'",
    "description": {"format": "markdown", "raw": "'"$DESCRIPTION"'"},
    "estimatedTime": "PT'"$HOURS"'H",
    "_links": {
      "type":   {"href": "/api/v3/types/'"$TASK_TYPE_ID"'"},
      "status": {"href": "/api/v3/statuses/'"$STATUS_NEW_ID"'"},
      "parent": {"href": "/api/v3/work_packages/'"$PARENT_STORY_ID"'"}
    }
  }' > /tmp/op_new_task.json
cat /tmp/op_new_task.json
```

**Returns:** `{ id, subject, url }`

---

## Operation: CREATE_SPRINT

Called by: `bellosoft-plan-epic` before pushing stories

In OpenProject, sprints are called **Versions**.

**Input:**
```
name: string        (e.g. "Sprint 3")
start_date: string  (YYYY-MM-DD)
end_date: string    (YYYY-MM-DD)
```

First check for existing version with same name:
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/versions" > /tmp/op_versions.json
cat /tmp/op_versions.json
```
If a version with the same name exists → confirm with user before creating duplicate.

If not exists → create:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/versions" \
  -d '{
    "name": "'"$NAME"'",
    "startDate": "'"$START_DATE"'",
    "endDate": "'"$END_DATE"'",
    "status": "open",
    "_links": {
      "definingProject": {"href": "/api/v3/projects/'"$PROJECT_ID"'"}
    }
  }' > /tmp/op_new_version.json
cat /tmp/op_new_version.json
```

**Returns:** `{ version_id, name }` — save `version_id` for use in CREATE_STORY.

---

## Operation: UPDATE

Called by: `bellosoft-sync` after dev milestones

**Input:**
```
work_package_id: number    (OpenProject WP id)
action: "transition" | "comment" | "assign"
status_name: string        (for transition — e.g. "In Progress", "In Review", "Done")
comment: string            (for comment — plain text)
assignee_id: number        (for assign)
```

**For all updates** — always fetch current `lockVersion` first:
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/work_packages/$WP_ID" > /tmp/op_wp_current.json
cat /tmp/op_wp_current.json
# Extract lockVersion from JSON
```

**Transition:**
1. Map `status_name` → status ID using profile or re-fetch `/api/v3/statuses`
2. PATCH with lockVersion:
```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/$WP_ID" \
  -d '{"lockVersion": '"$LOCK_VERSION"', "_links": {"status": {"href": "/api/v3/statuses/'"$STATUS_ID"'"}}}'
```

**Comment:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/$WP_ID/activities" \
  -d '{"comment": {"raw": "'"$COMMENT"'"}}'
```

**Assign:**
```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/$WP_ID" \
  -d '{"lockVersion": '"$LOCK_VERSION"', "_links": {"assignee": {"href": "/api/v3/users/'"$ASSIGNEE_ID"'"}}}'
```

**Hard rule:** Never transition to Done/Closed without explicit ✅ READY signal
from `bellosoft-dev-review` or explicit user instruction.

---

## Operation: GET

Called by: `bellosoft-dev-plan`, `bellosoft-sprint`

**Input:** `work_package_id: number` (OpenProject integer ID)

```bash
OP_URL=$(cat .secrets/op-url.txt | tr -d '\n')
OP_TOKEN=$(cat .secrets/op-api-token.txt | tr -d '\n')
curl -s \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/work_packages/{work_package_id}" > /tmp/op_wp.json
cat /tmp/op_wp.json
```

Parse and return structured object:
- `id`, `subject` (title)
- `description.raw` (markdown text)
- `estimatedTime` (duration, e.g. "PT8H")
- `status` — from `_links.status.title`
- `type` — from `_links.type.title`
- `assignee` — from `_links.assignee.title`
- `parent` — from `_links.parent.href` (extract ID)
- `version` — from `_links.version.title` (sprint name)
- `lockVersion` (save for potential PATCH)
- Extract acceptance criteria from `description.raw` — look for "Acceptance Criteria" heading

**Returns:** structured story object ready for `bellosoft-dev-plan` to consume.

---

## Operation: LIST_SPRINT

Called by: `bellosoft-sprint`

**Input:** `scope: "mine" | "team"`, `user_id: number (optional)`

1. Find active version (sprint):
```bash
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/versions" > /tmp/op_versions.json
cat /tmp/op_versions.json
```
Filter for `status: "open"` versions. If multiple, pick the most recently started.

2. Fetch work packages in that version:
```bash
FILTERS='[{"version":{"operator":"=","values":["'"$VERSION_ID"'"]}},{"status":{"operator":"!","values":["'"$DONE_STATUS_ID"'"]}}]'
curl -s -G \
  -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  --data-urlencode "filters=$FILTERS" \
  --data-urlencode "pageSize=100" > /tmp/op_sprint_wps.json
cat /tmp/op_sprint_wps.json
```

3. If `scope = "mine"` → filter results where `_links.assignee.href` contains the current user ID

Group by status name:
- Closed/Done statuses → ✅ Done
- "In Review" or "Code Review" → 🔵 In Review
- "In Progress" or "In Development" → 🟡 In Progress
- Statuses with `isDefault: true` or "New"/"To Do" → ⚪ To Do

**Returns:** grouped work package list with `id`, `subject`, `status`, `assignee`.

---

## Operation: SYNC_EPICS

Called by: `bellosoft-sync` (bulk push mode), or directly

Upsert every epic and story from `docs/planning-artifacts/epics.md` → OpenProject.
`docs/planning-artifacts/epics.md` is the source of truth — safe to re-run.

**Behavior:**
- Creates epics/stories not yet in OpenProject
- Updates subject/description if changed in epics.md
- Never changes status, assignees, or version on existing items
- Never deletes

**Steps:**
1. Read `docs/planning-artifacts/epics.md` — extract all epics and stories
2. Print full list: `"Push N epics, N stories to OpenProject? [y/n]"`
3. Fetch all existing work packages in the project (paginate with `pageSize=100`):
```bash
curl -s -G "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  --data-urlencode 'pageSize=100' \
  -H "Authorization: Bearer $OP_TOKEN" > /tmp/op_all_wps.json
```
Build `subject → id` lookup map.
4. Upsert epics (CREATE_EPIC for new; PATCH subject if changed — remember lockVersion)
5. Upsert stories (CREATE_STORY for new; PATCH if changed)
6. Update `docs/planning-artifacts/status.md` with OpenProject IDs (e.g. `op_epic_E1: 42`)

**Name matching:** strip `[OP-N]` suffix before comparing.

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

Fetch existing OpenProject structure → build `docs/planning-artifacts/epics.md` + `docs/planning-artifacts/status.md`.

**Steps:**
1. Fetch all work packages in the project (paginate)
2. Identify epics (work packages with `_links.type.title = "Epic"` or no parent)
3. For each epic, identify stories (work packages with `_links.parent.href` = epic URL)
4. Build `docs/planning-artifacts/epics.md` in bellosoft format
5. Build `docs/planning-artifacts/status.md` with OpenProject IDs
6. Update `docs/planning-artifacts/openproject-profile.md` with project metadata

Ask before overwriting if `docs/planning-artifacts/` already exists.

---

## Tracker detection (multi-tracker environments)

When more than one tracker may be configured:

1. Check `docs/planning-artifacts/status.md` for `tracker:` field
2. `tracker: openproject` → delegate here
3. `tracker: jira` → delegate to `bellosoft-jira`
4. `tracker: plane` → delegate to `bellosoft-plane`
5. Not set → check which profile files exist (`openproject-profile.md`, `jira-profile.md`, `plane-profile.md`)
6. Multiple exist → ask user which tracker for this operation
7. None → ask user to run setup for their preferred tracker

---

## How other bellosoft skills call this skill

**bellosoft-plan-epic** after approval:
```
→ bellosoft-openproject: create-sprint "Sprint 3" 2026-06-10 2026-06-24
→ bellosoft-openproject: create-epic E1 "User Auth" "Handles login, registration, JWT"
→ bellosoft-openproject: create-story E1-S1 ... epic_id=42 version_id=7
→ bellosoft-openproject: create-task E1-S1-T1 "Add users table migration" parent=55 area_tag=BE
```

**bellosoft-sync** after dev-review ✅ READY:
```
→ bellosoft-openproject: update 42 transition "In Review"
→ bellosoft-openproject: update 42 comment "Review passed. All ACs covered..."
```

**bellosoft-sprint**:
```
→ bellosoft-openproject: list-sprint mine
```

**bellosoft-dev-plan** (free-text flow, user wants ticket):
```
→ bellosoft-openproject: create-story ... (no epic, standalone)
```

---

## Error handling

- Log every failure, never silently drop
- Continue after individual failures — collect and report at the end
- For bulk operations (SYNC_EPICS): always produce markdown fallback for failed items
- HTTP 409 on PATCH = lockVersion mismatch → re-fetch WP, retry with new lockVersion (once)
- HTTP 422 = validation error → read `message` and `_embedded.errors` from response body
- Type ID not found → re-run SETUP to refresh type IDs
- Status ID not found → re-fetch `/api/v3/statuses` and update profile

---

## Hard rules

- Always load `references/api-guide.md` before any OpenProject operation
- Always resolve type IDs and status IDs from profile — never hardcode integers
- Always fetch `lockVersion` before any PATCH operation
- Always write API responses to a temp file; never pipe to jq or python3
- Always use `_links` HAL format to set relationships (status, type, parent, version, assignee)
- Confirm before any bulk operation > 10 items
- Never delete work packages or epics
- Never transition to Done without explicit ✅ READY signal
- `.secrets/` must always be gitignored — check on first write per session
