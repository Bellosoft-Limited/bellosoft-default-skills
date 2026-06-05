---
name: bellosoft-jira
description: >
  Central Jira integration layer for all bellosoft skills. Handles ALL Jira
  operations — create/update epics, stories, tasks, sprints, comments, and
  project scaffolding. Other bellosoft skills MUST delegate Jira operations here
  rather than calling Atlassian MCP tools directly. Triggers: /bellosoft-jira,
  "create jira epic", "push to jira", "update jira ticket", "sync to jira", or
  when any bellosoft skill needs to read/write Jira.
---

# Skill: bellosoft-jira

**This is the Jira service layer for the bellosoft ecosystem.**

All other bellosoft skills delegate Jira operations here. No other skill should
call Atlassian MCP tools directly — route through this skill instead.

```
/bellosoft-jira setup           ← first-time project scaffold
/bellosoft-jira create-epic     ← create epic (called by plan-epic)
/bellosoft-jira create-story    ← create story (called by plan-epic, dev-plan)
/bellosoft-jira create-task     ← create sub-task (called by plan-epic, plan-adhoc)
/bellosoft-jira create-sprint   ← create sprint (called by plan-epic)
/bellosoft-jira update          ← update state/comment (called by sync, dev-review)
/bellosoft-jira get             ← fetch issue by key (called by dev-plan, sprint)
/bellosoft-jira list-sprint     ← list active sprint (called by bellosoft-sprint)
/bellosoft-jira sync-epics      ← bulk push docs/planning-artifacts/epics.md → Jira
/bellosoft-jira import          ← import existing Jira project → docs/planning-artifacts/
```

---

## Step 0 — Always load first

**At the start of every invocation, load:**
```
references/jql-guide.md
```

This file contains the Jira API quirks, ADF format rules, custom field names,
issue type hierarchy, and JQL patterns. **Never skip this.**

---

## Step 1 — Setup and auth

**Goal: resolve all credentials and identifiers upfront. Never ask mid-operation.**

### Step 1a — Credentials (resolved during setup)

Jira REST API requires `JIRA_URL`, `JIRA_USERNAME` (email), and `JIRA_API_TOKEN` for all curl fallback calls.

**Always read credential files first. Run these exact commands:**

```bash
# On Windows (PowerShell):
if (Test-Path ".secrets/jira-url.txt")      { Get-Content ".secrets/jira-url.txt" -Raw }
if (Test-Path ".secrets/jira-username.txt") { Get-Content ".secrets/jira-username.txt" -Raw }
if (Test-Path ".secrets/jira-api-token.txt"){ Get-Content ".secrets/jira-api-token.txt" -Raw }
# On Mac/Linux (bash):
cat .secrets/jira-url.txt 2>/dev/null
cat .secrets/jira-username.txt 2>/dev/null
cat .secrets/jira-api-token.txt 2>/dev/null
```

**Resolution order for each value (stop at first success):**

1. **Read from `.secrets/jira-{url,username,api-token}.txt`** — run the commands above first
2. Check env vars: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`
3. Check `docs/planning-artifacts/jira-profile.md` for `jira_url` and `email` fields
4. Only if all above are missing, prompt once per missing value:
   - URL: `"What is your Jira URL? (e.g. https://yourorg.atlassian.net)"`
   - Username: `"What is your Jira email address?"`
   - API token: `"What is your Jira API token? (get it from id.atlassian.com → Security → API tokens)"`
5. Save each to its respective `.secrets/jira-{url,username,api-token}.txt` immediately
6. Ensure `.secrets/` is gitignored:
   ```bash
   grep -qxF '.secrets/' .gitignore || echo '.secrets/' >> .gitignore
   ```

All subsequent curl calls use: `-u "{username}:{api-token}" "{jira_url}/rest/api/3/..."`

### Step 1b — MCP connectivity (optional enhancement)

Try `mcp__atlassian__jira_get_myself()` silently. If it succeeds, use MCP tools for reads (faster).
If it fails or is unavailable, fall back to REST API for all operations — **do not stop**.
MCP is a convenience, not a requirement.

### Step 1c — User identity

**Resolution order:**

1. Check `docs/planning-artifacts/jira-profile.md` — if `account_id` present, use silently
2. MCP available → use identity from Step 1b result
3. REST fallback:
   ```bash
   curl -s -u "{username}:{api-token}" "{jira_url}/rest/api/3/myself"
   ```
   Extract: `displayName`, `accountId`, `emailAddress`
4. Save to `docs/planning-artifacts/jira-profile.md`:
   ```markdown
   # Jira Profile
   - **display_name**: [name]
   - **account_id**: [accountId]
   - **email**: [emailAddress]
   - **jira_url**: [url]
   ```

### Step 1d — Project resolution

1. Check `docs/planning-artifacts/status.md` for `jira_project_key:` — use silently if found
2. Else list projects via MCP (`mcp__atlassian__jira_get_all_projects()`) or REST:
   ```bash
   curl -s -u "{username}:{api-token}" "{jira_url}/rest/api/3/project/search"
   ```
   - One project → use silently, notify: `"Using project: {KEY} ({name})"`
   - Multiple → list and ask which to use
   - None → offer: `"No projects found. Type 'create' to scaffold one."` → CREATE_PROJECT
3. Store in `docs/planning-artifacts/status.md` under `jira_project_key:`

---

## Critical API Rules

These rules are non-negotiable. Violating them causes Jira API errors:

| Concern | ❌ Wrong | ✅ Correct |
|---------|---------|-----------|
| Issue description | plain string | ADF object (see jql-guide.md) |
| Epic link (next-gen) | `Epic Link` field | `parent` field with epic issue key |
| Epic link (classic) | `parent` field | `customfield_10014` = epic key |
| Story points | `story_points` | discover via `jira_get_fields` first |
| Sprint assignment | `sprint` | `customfield_10020` = sprint ID (integer, not name) |
| Transitions | status name | `jira_get_issue_transitions` → use transition ID |
| Subtask parent | `subtask` type only | `parent: {key: "PROJ-123"}` |
| Issue type name | hardcode "Story" | discover via `jira_get_issue_types` first |

**Project type matters:**
- **Next-gen (team-managed):** Epics are issues with type "Epic"; stories use `parent` field
- **Classic (company-managed):** Epics use `customfield_10014`; subtasks need `parent` field

**Always detect project type at setup:**
```
mcp__atlassian__jira_search(jql="project = {KEY} AND issuetype = Epic", max_results=1)
```
Store detected type in `docs/planning-artifacts/jira-profile.md`.

**ADF format for descriptions:**
```json
{
  "type": "doc",
  "version": 1,
  "content": [
    { "type": "paragraph", "content": [{ "type": "text", "text": "Your text" }] }
  ]
}
```
See `references/jql-guide.md` for full ADF patterns.

**Custom field discovery:**
Always discover before first use — never assume field IDs:
```
mcp__atlassian__jira_get_fields()
```
Filter by name for: "Story Points", "Story point estimate", "Sprint", "Epic Link", "Epic Name".
Cache results in session. Store discovered IDs in `docs/planning-artifacts/jira-profile.md`.

---

## Operation: SETUP

Runs automatically on first use (triggered by Step 1 above). Discovers and caches
everything needed so subsequent operations never need to ask questions.

**ALREADY CONFIGURED CHECK — run this first:**
1. Check if `docs/planning-artifacts/jira-profile.md` exists and contains `project_key`, `account_id`, and `issue_types`
2. If complete → **stop immediately** and report:
   ```
   ✅ Jira already configured:
     Project: {project_key} ({project_name})
     Type: {project_type}
     User: {display_name} ({email})
     Issue types: Epic, Story, Task, Sub-task, Bug
   No setup needed. To refresh, delete docs/planning-artifacts/jira-profile.md first.
   ```
3. Only proceed with discovery steps below if profile is missing or incomplete.

**Steps (only if not already configured):**
1. Identity + project already resolved in Step 1 — reuse, no extra calls
2. `mcp__atlassian__jira_get_issue_types(project_key)` → save type IDs
3. `mcp__atlassian__jira_get_fields()` → save custom field IDs (story points, sprint, epic link)
4. Detect project type: search for one Epic issue — if found, record type
5. Save all to `docs/planning-artifacts/jira-profile.md`

SETUP is silent and automatic. It does not ask the user any questions.

**Output `docs/planning-artifacts/jira-profile.md`:**
```markdown
# Jira Profile
- **display_name**: ...
- **account_id**: ...
- **email**: ...
- **project_key**: PROJ
- **project_type**: next-gen | classic
- **board_id**: 42
- **issue_types**:
  - Epic: 10000
  - Story: 10001
  - Task: 10002
  - Sub-task: 10003
  - Bug: 10004
- **custom_fields**:
  - story_points: customfield_10058
  - sprint: customfield_10020
  - epic_link: customfield_10014 (classic only)
```

---

## Operation: CREATE_PROJECT

Called by: tracker bootstrap (when user has no Jira project)

Creates a new Jira project with bellosoft-standard configuration.

**Input:**
```
project_name: string     (e.g. "My App")
project_key: string      (e.g. "MYAPP" — 2-10 uppercase letters, must be unique)
project_type: "scrum" | "kanban" | "next-gen"
lead_account_id: string  (from jira-profile.md — current user)
```

**Key selection rules:**
- Suggest key from first letters of project name words (e.g. "My App" → "MA")
- Check uniqueness: if key conflicts → suggest , 
- User confirms before creating

**Steps:**

1. Confirm project details with user:
   ```
   Creating Jira project:
     Name: {project_name}
     Key:  {project_key}
     Type: {project_type}
   Proceed? [y/n]
   ```

2. Create via MCP:
   ```
   mcp__atlassian__jira_create_project(
     name = "{project_name}",
     key = "{project_key}",
     project_type_key = "software",
     project_template_key = "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum"
   )
   ```

   If MCP does not expose project creation → provide REST curl:
   ```bash
   curl -s -X POST      "{JIRA_URL}/rest/api/3/project"      -u "{JIRA_USERNAME}:{JIRA_API_TOKEN}"      -H "Content-Type: application/json"      -d '{
       "name": "{project_name}",
       "key": "{project_key}",
       "projectTypeKey": "software",
       "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
       "leadAccountId": "{lead_account_id}"
     }'
   ```

3. After creation, run SETUP automatically to discover issue types, custom fields, board ID.

4. Save to :
   ```
   tracker: jira
   jira_project_key: {project_key}
   ```

5. Output:
   ```
   ✅ Jira project created: {project_name} ({project_key})
      Board URL: {JIRA_URL}/jira/software/projects/{project_key}/boards
      Setup complete — issue types, fields, and board ID saved to docs/planning-artifacts/jira-profile.md
   ```

**Project template options (for Scrum teams):**
- Scrum: 
- Kanban: 
- Next-gen Scrum: 

---

## Operation: CREATE_EPIC

Called by: `bellosoft-plan-epic` after approval

**Input:**
```
title: string
description: string (plain text — skill converts to ADF)
epic_number: string (e.g. "E1")
```

**Execution:**

Load `docs/planning-artifacts/jira-profile.md`. Build ADF description:
```json
{
  "type": "doc", "version": 1,
  "content": [
    { "type": "paragraph", "content": [{ "type": "text", "text": "{description}" }] },
    { "type": "paragraph", "content": [
      { "type": "text", "text": "Source: docs/planning-artifacts/epics.md — Epic {epic_number}",
        "marks": [{"type": "em"}] }
    ]}
  ]
}
```

Create issue:
```
mcp__atlassian__jira_create_issue(
  project_key = "{KEY}",
  summary = "Epic {N}: {title}",
  issue_type = "Epic",
  description = {ADF object},
  additional_fields = { "labels": ["ai-generated"] }
)
```

For **classic projects**, also set in additional_fields:
```json
{ "customfield_10011": "{title}" }
```
(Epic Name field — required in classic)

**Returns:** `{ epic_key (e.g. PROJ-5), id, url }`

---

## Operation: CREATE_STORY

Called by: `bellosoft-plan-epic`, `bellosoft-dev-plan` (free-text flow), `bellosoft-plan-adhoc`

**Input:**
```
title: string
user_story: string ("As a ... I want ... so that ...")
acceptance_criteria: string[]
epic_key: string (e.g. PROJ-5)
sprint_id: number (optional)
estimate_hours: number
priority: "Highest" | "High" | "Medium" | "Low" | "Lowest"
assignee_id: string (optional — account_id)
labels: string[] (optional)
```

**Execution:**

Build ADF description with user story + acceptance criteria list.
See `references/jql-guide.md` for the story ADF template.

Build `additional_fields`:
```json
{
  "{story_points_field}": {estimate_hours},
  "timetracking": { "originalEstimate": "{estimate_hours}h" },
  "customfield_10020": {sprint_id},
  "labels": {labels},
  "priority": {"name": "{priority}"},
  "assignee": {"accountId": "{assignee_id}"}
}
```

⚠️ **`{story_points_field}` must be resolved before this call.** If `jira-profile.md` does not contain `story_points` under `custom_fields`, run:
```
mcp__atlassian__jira_get_fields()
```
or REST:
```bash
curl -s -u "{username}:{api-token}" "{jira_url}/rest/api/3/field" | ConvertFrom-Json | Where-Object { $_.name -match "story point|estimate" }
```
Cache the field ID in `jira-profile.md`. **Never skip this — a missing field ID silently drops the estimate.**

```json
```

For **next-gen**: add `"parent": {"key": "{epic_key}"}` to additional_fields.
For **classic**: add `"customfield_10014": "{epic_key}"` instead.

```
mcp__atlassian__jira_create_issue(
  project_key = "{KEY}",
  summary = "{title}",
  issue_type = "Story",
  description = {ADF object},
  additional_fields = {fields}
)
```

Add source comment after creation:
```
mcp__atlassian__jira_add_comment(
  issue_key = "{key}",
  comment = "Created by bellosoft-plan-epic from docs/planning-artifacts/epics.md"
)
```

**Returns:** `{ story_key (e.g. PROJ-12), id, url }`

---

## Operation: CREATE_TASK

Called by: `bellosoft-plan-epic` (sub-tasks), `bellosoft-plan-adhoc`

**Input:**
```
title: string                (task description, without tag prefix)
task_id: string              (e.g. "E1-S1-T1" — epic.story.task numbers)
acceptance_criterion: string
estimate_hours: number
parent_story_key: string     (e.g. PROJ-12)
area_tag: string             (BE/FE/DB/QA/INFRA/etc.)
labels: string[]             (optional)
```

**Task summary format:** `{task_id} [{TAG}] {title}`
Example: `E1-S1-T1 [FW] Update TargetFramework to net10.0 in all 4 .csproj files`

**Issue type selection:**
- Parent provided → use "Sub-task" type with `parent` field
- Standalone → use "Task" type (no parent)

**Execution:**

Build ADF description:
```json
{
  "type": "doc", "version": 1,
  "content": [
    { "type": "heading", "attrs": {"level": 3},
      "content": [{"type": "text", "text": "Acceptance Criterion"}] },
    { "type": "paragraph", "content": [{"type": "text", "text": "{AC}"}] },
    { "type": "paragraph", "content": [
      {"type": "text", "text": "Estimate: {N}h", "marks": [{"type": "strong"}]}
    ]}
  ]
}
```

```
mcp__atlassian__jira_create_issue(
  project_key = "{KEY}",
  summary = "{task_id} [{TAG}] {title}",
  issue_type = "Sub-task",
  description = {ADF},
  additional_fields = {
    "parent": {"key": "{parent_story_key}"},
    "{story_points_field}": {estimate_hours},
    "timetracking": { "originalEstimate": "{estimate_hours}h" },
    "labels": {labels}
  }
)
```

**Returns:** `{ task_key, id, url }`

---

## Operation: CREATE_SPRINT

Called by: `bellosoft-plan-epic` before pushing stories

**Input:**
```
name: string        (e.g. "Sprint 3")
start_date: string  (ISO-8601: 2026-06-10T00:00:00.000Z)
end_date: string    (ISO-8601: 2026-06-24T00:00:00.000Z)
board_id: number    (from jira-profile.md)
```

First check for existing sprint with same name:
```
mcp__atlassian__jira_search(
  jql = 'project = {KEY} AND sprint = "{name}"',
  max_results = 1
)
```

If exists → confirm with user before creating duplicate.

If not exists → create:
```
mcp__atlassian__jira_create_sprint(
  board_id = {board_id},
  name = "{name}",
  start_date = "{start_date}",
  end_date = "{end_date}"
)
```

If `jira_create_sprint` is unavailable → inform user and output the curl command:
```bash
curl -s -X POST \
  "{JIRA_URL}/rest/agile/1.0/sprint" \
  -H "Authorization: Bearer {JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"{name}","startDate":"{start_date}","endDate":"{end_date}","originBoardId":{board_id}}'
```

**Returns:** `{ sprint_id, name }`

---

## Operation: UPDATE

Called by: `bellosoft-sync` after dev milestones

**Input:**
```
issue_key: string          (e.g. PROJ-42)
action: "transition" | "comment" | "assign"
status_name: string        (for transition — e.g. "In Progress", "In Review", "Done")
comment: string            (for comment — plain text)
assignee_id: string        (for assign — account_id)
```

**Transition:**
1. `mcp__atlassian__jira_get_issue_transitions(issue_key)` → map name → transition ID
2. Find by name (case-insensitive partial match)
3. `mcp__atlassian__jira_transition_issue(issue_key, transition_id)`

**Comment:**
```
mcp__atlassian__jira_add_comment(issue_key, comment)
```

**Assign:**
```
mcp__atlassian__jira_update_issue(
  issue_key,
  fields = { "assignee": { "accountId": "{assignee_id}" } }
)
```

**Hard rule:** Never transition to Done/Closed without explicit ✅ READY signal
from `bellosoft-dev-review` or explicit user instruction.

---

## Operation: GET

Called by: `bellosoft-dev-plan`, `bellosoft-sprint`

**Input:** `issue_key: string` (e.g. PROJ-42)

```
mcp__atlassian__jira_get_issue(issue_key)
```

Parse and return structured object:
- `key`, `summary`, `description` (extract text from ADF)
- `status.name`, `assignee.displayName`, `priority.name`
- `acceptance_criteria` — extract from ADF (look for "Acceptance Criteria" heading)
- `sprint` — from `customfield_10020`
- `story_points` — from discovered story points field
- `parent` — epic key if set

**Returns:** structured story object ready for `bellosoft-dev-plan` to consume.

---

## Operation: LIST_SPRINT

Called by: `bellosoft-sprint`

**Input:** `scope: "mine" | "team"`, `account_id: string (optional)`

Build JQL:
- "mine" → `assignee = currentUser() AND sprint in openSprints() AND project = {KEY}`
- "team" → `sprint in openSprints() AND project = {KEY}`

```
mcp__atlassian__jira_search(
  jql = "{JQL} ORDER BY priority DESC, updated DESC",
  fields = "summary,status,assignee,priority,issuetype,{story_points_field}",
  max_results = 100
)
```

Group by status category: `To Do` ⚪, `In Progress` 🟡, `In Review` 🔵, `Done` ✅.
Issues with "Blocked" label or active blocker links → 🔴.

**Returns:** grouped issue list with `key`, `summary`, `status`, `assignee`, `priority`.

---

## Operation: SYNC_EPICS

Called by: `bellosoft-sync` (bulk push mode), or directly

Upsert every epic and story from `docs/planning-artifacts/epics.md` → Jira.
`docs/planning-artifacts/epics.md` is the source of truth — safe to re-run.

**Behavior:**
- Creates epics/stories not yet in Jira
- Updates summary/description if changed in epics.md
- Never changes status, assignees, labels, or priority on existing items
- Never deletes

**Steps:**
1. Read `docs/planning-artifacts/epics.md` — extract all epics and stories
2. Print full list: `"Push N epics, N stories to Jira? [y/n]"`
3. Search existing: `jql="project={KEY} AND labels=ai-generated"`
   Build summary → key lookup map
4. Upsert epics (CREATE_EPIC for new, `jira_update_issue` for changed summary)
5. Upsert stories (CREATE_STORY for new, update for changed)
6. Update `docs/planning-artifacts/status.md` with Jira keys (e.g. `jira_epic_E1: PROJ-5`)

**Name matching:** strip `[PROJ-N]` suffix before comparing.

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

Fetch existing Jira project structure → build `docs/planning-artifacts/epics.md` + `docs/planning-artifacts/status.md`.

**Steps:**
1. Fetch all epics: `jql="project={KEY} AND issuetype=Epic ORDER BY created ASC"`
2. For each epic, fetch stories: `jql="project={KEY} AND issuetype=Story AND parent={epic_key}"`
3. Build `docs/planning-artifacts/epics.md` in bellosoft format
4. Build `docs/planning-artifacts/status.md` with all Jira keys
5. Update `docs/planning-artifacts/jira-profile.md` with project metadata

Ask before overwriting if `docs/planning-artifacts/` already exists.

---

## Tracker detection (multi-tracker environments)

When both Jira and Plane may be configured:

1. Check `docs/planning-artifacts/status.md` for `tracker:` field
2. `tracker: jira` → delegate here
3. `tracker: plane` → delegate to `bellosoft-plane`
4. Not set → check which profile files exist
5. Both exist → ask user which tracker for this operation
6. Neither → ask user to run `/bellosoft-jira setup` or `/bellosoft-plane setup`

---

## How other bellosoft skills call this skill

**bellosoft-plan-epic** after approval:
```
→ bellosoft-jira: create-sprint "Sprint 3" 2026-06-10 2026-06-24
→ bellosoft-jira: create-epic E1 "User Auth" "Handles login, registration, JWT"
→ bellosoft-jira: create-story E1-S1 ... epic_key=PROJ-5 sprint_id=42
→ bellosoft-jira: create-task E1-S1-T1 "[DB] Add users table" parent=PROJ-12
```

**bellosoft-sync** after dev-review ✅ READY:
```
→ bellosoft-jira: update PROJ-42 transition "In Review"
→ bellosoft-jira: update PROJ-42 comment "Review passed. All ACs covered..."
```

**bellosoft-sprint**:
```
→ bellosoft-jira: list-sprint mine
```

**bellosoft-dev-plan** (free-text flow, user wants ticket):
```
→ bellosoft-jira: create-story ... (no epic, standalone)
```

---

## Error handling

- Log every failure, never silently drop
- Continue after individual failures — collect and report at the end
- For bulk operations (SYNC_EPICS): always produce markdown fallback for failed items
- HTTP 400 on custom fields → re-run field discovery, IDs may have changed
- ADF validation errors → check jql-guide.md ADF section and rebuild
- "Issue type not found" → re-run SETUP to refresh issue type IDs
- Sprint MCP unavailable → provide curl command for manual sprint creation

---

## Hard rules

- Always load `references/jql-guide.md` before any Jira operation
- Always discover custom field IDs — never hardcode `customfield_*` values
- Always use ADF objects for descriptions — never plain strings
- Always use `parent` field for next-gen epics — not `customfield_10014`
- Always fetch transition IDs — never hardcode status transition IDs
- Confirm before any bulk operation > 10 items
- Never delete issues or epics
- Never transition to Done without explicit ✅ READY signal
- Store sprint IDs (integers) not sprint names in sprint field
