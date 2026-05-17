# Plane Lifecycle Workflow

Sync Plane tickets with BMAD story lifecycle events. All changes go through Plane MCP — never the UI.

---

## Setup

**Config:** Load from `{project-root}/_bmad/bmm/config.yaml`:

- `project_name` — used to auto-select the Plane project
- `planning_artifacts` (default: `{project-root}/docs/planning-artifacts`) → `epics.md`
- `implementation_artifacts` (default: `{project-root}/docs/implementation-artifacts`) → story files and `sprint-status.yaml`

**Project resolution:** Call `mcp_plane_list_projects`. Match `project_name` case-insensitively.

- Match found → auto-select silently.
- No match, one project → default to it, notify user.
- No match, multiple projects → present list and ask user to choose.

Store `project_id` and call `mcp_plane_list_states` once per session. Build the status map — show it to the user before the first update.

---

## Plane API Hard Rules

> Discovered through live execution. Violating these causes pydantic validation errors.

| Tool                                         | ❌ Wrong                                   | ✅ Correct                                                         | Notes                                                                                                                                                                                                                                                          |
| -------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mcp_plane_update_work_item`                 | `state_id=`                                | `state=`                                                           | Always `state=`, never `state_id=`                                                                                                                                                                                                                             |
| `mcp_plane_create_work_item`                 | `state_id=`, `parent_id=`                  | `state=`, `parent=`                                                | —                                                                                                                                                                                                                                                              |
| Any create/update                            | `description=`                             | `description_html=`                                                | Must be **real HTML** — compact, single-line, no `\n` between tags. Wrap in `<div>`. Allowed tags: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<code>`. ❌ No `<table>`, `<hr>`, markdown syntax, whitespace/indentation between tags. |
| `mcp_plane_search_work_items`                | any usage                                  | **AVOID — returns empty results**                                  | Use `mcp_plane_retrieve_work_item_by_identifier` instead                                                                                                                                                                                                       |
| `mcp_plane_retrieve_work_item_by_identifier` | `identifier=`                              | `issue_identifier=` (int) + `project_identifier=` (string)         | **Primary lookup method** — always use this when sequence_id is known                                                                                                                                                                                          |
| `mcp_plane_create_work_item_comment`         | `data=`                                    | `comment_html=`                                                    | Same HTML rules as `description_html` — compact, real HTML, no markdown                                                                                                                                                                                        |
| Properties endpoint                          | `GET /properties/` or `/issue-properties/` | `GET /work-item-types/{id}/work-item-properties/`                  | Only this path returns 200                                                                                                                                                                                                                                     |
| Properties `property_type`                   | lowercase values                           | uppercase: `TEXT`, `DATETIME`, `URL`, `OPTION`, `BOOLEAN`, `FILE`  | `text` / `date` / `datetime` all return 400                                                                                                                                                                                                                    |
| TEXT property settings                       | omit `settings`                            | `{"settings": {"display_format": "single-line"}}` or `"multi-line"` | Must be in **POST body at creation**. PATCH **can** fix it after creation too. Valid values: `"single-line"` (single line), `"multi-line"` (paragraph)                                                                                                    |

**Pagination:** All list calls: `per_page=100` + `cursor=`; repeat until `next_cursor` is null.

---

## Status Mapping

| bmad status      | Plane state name (case-insensitive) |
| ---------------- | ----------------------------------- |
| `ready-for-dev`  | `Todo`                              |
| `in-progress`    | `In Development`                    |
| `done` (dev)     | `In Development`                    |
| `review`         | `In Review`                         |
| `ready-for-qa`   | `In Review`                         |
| `done` (QA pass) | `Done`                              |

---

## Command Routing

Detect intent from what the user says and the current story file state:

| Signal                                                                         | Slash alias                 | Command        |
| ------------------------------------------------------------------------------ | --------------------------- | -------------- |
| `update plane` / `plane` / invoked after a BMAD skill                          | `/bellosoft-plane`          | AUTO_DETECT    |
| `sync epics to plane` / `plane sync epics` / `upload epics` / `upload stories` | `/bellosoft-plane-epics`    | SYNC_EPICS     |
| `sync sprint to plane` / `plane sync sprint`                                   | `/bellosoft-plane-sprint`   | SYNC_SPRINT    |
| `create plane project` / `scaffold plane project`                              | `/bellosoft-plane-scaffold` | CREATE_PROJECT |

If ambiguous, present the options and ask.

---

## AUTO_DETECT

When the user says `"update plane"`, `"plane"`, or this skill is triggered after a BMAD skill completes, infer the lifecycle event automatically.

**Story identification:** Use the provided story ID/path, or find the most recently modified `.md` in `{implementation_artifacts}`. Read the file fully.

**Event inference table:**

| Story file signals                                                     | Inferred event  |
| ---------------------------------------------------------------------- | --------------- |
| `Status: ready-for-dev` AND no Dev Agent Record section                | STORY_CREATED   |
| `Status: in-progress`                                                  | DEV_IN_PROGRESS |
| `Status: done` AND Dev Agent Record present AND no Code Review section | DEV_DONE        |
| Code Review section present (any status)                               | REVIEW_DONE     |

Show the inferred event to the user and confirm before updating Plane:

```
Detected: [event] for Story {id}: {title}
→ Will move Plane ticket to: {state}
Proceed? [y/n]
```

Then execute the appropriate handler below.

---

## STORY_CREATED

Triggered after `bmad-create-story` completes (`Status: ready-for-dev`).

Find the Plane work item using the **reliable lookup sequence**:

1. Parse `sequence_id` from the current git branch name if it follows `{type}/{identifier}-{N}-{slug}` pattern.
2. Otherwise call `mcp_plane_list_work_items` with `project_id` + `per_page=100`, filter in memory for `name` containing `Story {story_id}`.
3. Call `mcp_plane_retrieve_work_item_by_identifier` with `issue_identifier={sequence_id}` (integer) and `project_identifier={project.identifier}`.

- ⚠️ Do NOT use `mcp_plane_search_work_items` — it consistently returns empty results.
- If not found: halt with `"No Plane ticket found for Story {story_id}. Run 'sync epics to plane' first."`

Resolve the user's Plane member ID (see **Member ID Resolution** below).

Update with `mcp_plane_update_work_item`:

- `state`: In Development state ID
- `assignees`: `[plane_member_id]`
- `description_html`: user story + acceptance criteria rendered as HTML. **Do NOT include the story title** — the work item `name` field already holds it.

---

## DEV_IN_PROGRESS

Triggered when story `Status: in-progress` (dev has started).

Find the work item using `mcp_plane_retrieve_work_item_by_identifier` (parse `sequence_id` from branch name or list+filter). Update `state` to In Development if not already there. No description update needed.

---

## DEV_DONE

Triggered when `Status: done` + Dev Agent Record present, no Code Review section.

Find the work item using `mcp_plane_retrieve_work_item_by_identifier` (parse `sequence_id` from branch name or list+filter). Update `state` to In Development (stays — code review comes next).

Scan the Dev Agent Record for anything a PM must know: deviations from the original plan, deferred items, discovered constraints, scope changes, or files that differ from what was planned. If anything noteworthy exists, add a comment via `mcp_plane_create_work_item_comment`. If implementation went exactly as planned, skip the comment.

Comment format (only if noteworthy content exists):

```
<p>🛠️ <strong>Dev Complete</strong> — Story {story_id}</p><p><strong>Notes for PM</strong></p><ul><li>{each deviation / constraint / deferred item}</li></ul>
```

Do NOT update `description_html`.

---

## REVIEW_DONE

Triggered when a Code Review section is present in the story file.

Find the work item using `mcp_plane_retrieve_work_item_by_identifier` (parse `sequence_id` from branch name or list+filter).

**Auto-run tests:**

- **Backend:** look for `src/AutomaLead.Tests.Security/Story{N}_{M}_*.cs`. If found:
  ```
  cd src && dotnet test AutomaLead.Tests.Security/AutomaLead.Tests.Security.csproj --filter "FullyQualifiedName~Story{N}_{M}" -v normal
  ```
- **Frontend:** look for `src/AutomaLead.Web/e2e/story-{N}-{M}-*.spec.ts`. If found:
  ```
  cd src/AutomaLead.Web && npx playwright test e2e/story-{N}-{M}-*.spec.ts --reporter=list
  ```
- If tests fail: warn the user and ask: `Tests failing — fix first, or proceed to In Review anyway? [fix / proceed]`
- If neither test file exists: note "No automated tests found" and continue.

Update `state` to In Review.

Scan the Code Review findings for deferred items, scope changes, security concerns, or blockers.

Always add a comment via `mcp_plane_create_work_item_comment` (`comment_html=`):

**If tests ran:**

```html
<p>🔍 <strong>Code Review Complete</strong> — Story {story_id}: {story_title}</p><p><strong>Test Results</strong><br/>Total: N | Passed: N | Failed: 0 | Duration: Xs</p><p>{test names, max 30 lines — truncate with "…and N more"}</p><p>{if deferred findings: <strong>Deferred Findings</strong><ul><li>...</li></ul>}</p><p>Moved to In Review on {date}.</p>
```

**If no tests found and deferred findings exist:**

```html
<p>🔍 <strong>Code Review Complete</strong> — Story {story_id}</p>
<p><strong>Deferred / Notable Findings</strong></p>
<ul>
  <li>{each finding}</li>
</ul>
```

**If no tests and no deferred findings:** skip the comment.

Do NOT update `description_html`.

---

## SYNC_EPICS

Upsert every epic and story from `planning-artifacts/epics.md` into Plane. **epics.md is the single source of truth** — when content changes there, this command updates Plane to match. Safe to re-run.

**Behavior:**
- Creates new epics/stories that don't exist in Plane
- Updates existing epics/stories when name or description in epics.md has changed
- Skips items that are already in sync
- Never changes workflow state, labels, assignees, or other user-managed fields
- Only updates: `name`, `description_html`, `parent` (for stories)

**Step 1 — Scan & list before doing anything:**
Read `planning-artifacts/epics.md`. Extract all epics and stories. Print the full list to the user before any API calls:

```
Found:
  Epic 1: <title>  (N stories)
  Epic 2: <title>  (N stories)
  ...
  Total: X epics, Y stories
Proceed? [y/n]
```

**Step 2 — Create project (with identifier collision handling):**

⚠️ **Plane enforces globally-unique identifiers across ALL workspace projects.** `HTTP 409 Conflict` means the identifier is taken.

**Identifier strategy:**
1. Try `identifier` (user's chosen value).
2. If 409: append digit → `{identifier}2`, `{identifier}3`, etc. (max 3 retries).
3. If all fail: fall back to initials of each word in `project_name`, uppercased, max 12 chars.
4. If STILL 409: ask user for a new identifier.

**⚠️ `is_time_tracking_enabled` causes 400 Bad Request** — Plane's API silently rejects it. Never pass this field.

Call `mcp_plane_create_project`:

- `name`: project_name
- `identifier`: IDENTIFIER (uppercase)
- `timezone`: `America/Sao_Paulo`
- `cycle_view`: true
- `is_issue_type_enabled`: true
- `project_lead`: invoking user's `plane_member_id`

Store the returned `project_id` and `identifier` for all subsequent steps.

**⚠️ Ambiguous matching alert:** If the user says "it created the project" after multiple 409s and retries with different identifiers, the project may exist under a retried identifier. Use `curl` to list all workspace projects and match by `name` case-insensitively to find the actual `project_id`:
```
curl -s "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/" -H "x-api-key: {key}"
```

**Step 3 — Build existence lookups:**
Fetch all existing epics (paginate `mcp_plane_list_epics`) and work items (paginate `mcp_plane_list_work_items`). Build case-insensitive lookups by `name.toLowerCase()`.

**Important:** Store the full epic/work item objects (including `id`, `sequence_id`, `name`, `description_html`, `parent`) — needed for comparison in Steps 5 and 6 to detect content changes.

**Step 4 — Resolve label ID:**
Fetch labels via `mcp_plane_list_labels`. Find `bmad-generated` label by name (case-insensitive). If not found, create it with color `#7C3AED` via `mcp_plane_create_label`. Store the label ID.

**Step 5 — Parse epics.md:**

- Epics: `### Epic N: <Title>` (H3, under `## Epic List`) — extract number, title, and the first descriptive paragraph (the italic line starting with `_`)
- Stories: `### Story N.M: <Title>` (H3) — extract: story_id, title, user story ("As a..." paragraph), acceptance criteria (Given/When/Then blocks under **Acceptance Criteria:**)
- **Process in file order (ascending)** — Epic 1 before Epic 2, Story N.1 before Story N.2, etc. Do NOT sort or reorder.

**Name comparison rules:**
When checking if an epic/story exists in Plane:
- Strip the `[IDENTIFIER-seq]` suffix from both the epics.md title and Plane name before comparing
- Example: `Epic 11 [CA3-54]: MCP Data Access Tools` → compare as `Epic 11: MCP Data Access Tools`
- This allows the workflow to find items even when the identifier has been written back
- Case-insensitive match on the stripped name

**Step 5 — Upsert epics** via `mcp_plane_create_epic` or update if content changed:

**For each epic in epics.md:**

1. Build expected values from epics.md:
   - `expected_name`: epic title with [IDENTIFIER-seq] if present, e.g. `Epic 1 [CA3-2]: Infrastructure Foundations`
   - `expected_description_html`: compact HTML of the epic's first descriptive paragraph (the italic line starting with `_`)

2. Check existence lookup (from Step 2):
   - If epic name (ignoring `[IDENTIFIER-seq]` suffix) found → **UPDATE PATH**
   - If not found → **CREATE PATH**

3. **CREATE PATH:**
   - Call `mcp_plane_create_epic` with:
     - `name`: `expected_name`
     - `description_html`: `expected_description_html`
     - `label_ids`: `[bmad-generated label ID]`
   - Record the `sequence_id` from response — needed in Step 7.

4. **UPDATE PATH (epics.md is source of truth):**
   - Retrieve the existing epic's current `name` and `description_html`
   - Compare with expected values:
     - Name differs (ignoring whitespace)? → UPDATE
     - Description differs (ignoring whitespace)? → UPDATE
   - If either field differs, call `mcp_plane_update_epic` with:
     - `name`: `expected_name`
     - `description_html`: `expected_description_html`
   - **Never change `state`** on existing epics — preserve user's workflow state
   - **Never change `labels`, `assignees`, `priority`, etc.** — only update name and description
   - Record the existing `sequence_id` (from lookup) — needed in Step 7.
   - If updated, log: `Updated Epic {epic_id}: name/description changed in epics.md`

5. **Skip criteria:**
   - Only skip (no API call) if name AND description match exactly
   - Log: `Skipped Epic {epic_id}: already in sync`

**Step 6 — Upsert stories** via `mcp_plane_create_work_item` or update if content changed:

**For each story in epics.md:**

1. Build expected values from epics.md:
   - `expected_name`: story title with [IDENTIFIER-seq] if present, e.g. `Story 1.2 [CA3-19]: Security Hardening — ...`
   - `expected_description_html`: compact HTML — user story `<p>` + `<h3>Acceptance Criteria</h3>` + `<ul>` of criteria items
   - `expected_parent_id`: epic work item ID (from Step 5)

2. Check existence lookup (from Step 2):
   - If story name (ignoring `[IDENTIFIER-seq]` suffix) found → **UPDATE PATH**
   - If not found → **CREATE PATH**

3. **CREATE PATH:**
   - Call `mcp_plane_create_work_item` with:
     - `name`: `expected_name`
     - `description_html`: `expected_description_html`
     - `parent`: `expected_parent_id`
     - `state`: Backlog state ID
     - `label_ids`: `[bmad-generated label ID]`
   - After creating, add a traceability comment via `mcp_plane_create_work_item_comment`:
     ```
     <p><strong>Source:</strong> docs/planning-artifacts/epics.md — Story {story_id}</p>
     ```
   - Record the `sequence_id` from response — needed in Step 7.

4. **UPDATE PATH (epics.md is source of truth):**
   - Retrieve the existing work item's current `name`, `description_html`, and `parent`
   - Compare with expected values:
     - Name differs (ignoring whitespace)? → UPDATE
     - Description differs (ignoring whitespace)? → UPDATE
     - Parent differs? → UPDATE
   - If any field differs, call `mcp_plane_update_work_item` with:
     - `name`: `expected_name`
     - `description_html`: `expected_description_html`
     - `parent`: `expected_parent_id`
   - **Never change `state`** on existing items — preserve user's workflow state
   - **Never change `labels`, `assignees`, `priority`, etc.** — only update name, description, parent
   - Record the existing `sequence_id` (from lookup) — needed in Step 7.
   - If updated, log: `Updated Story {story_id}: name/description changed in epics.md`

5. **Skip criteria:**
   - Only skip (no API call) if name, description, AND parent all match exactly
   - Log: `Skipped Story {story_id}: already in sync`

**Step 7 — Summary &amp; offer sync:**
```
✅ Project scaffolded: {project_name} ({IDENTIFIER})
  States:     8 configured (N created, M updated, K deleted)
  Labels:     N created, M skipped
  Work types: N created, M skipped (Task was default — reused)

⚠️  Icon/color for work item types must be set manually in the Plane UI
    (Project Settings → Work item types):
      Task        → default icon  · #6695FF
      Bug         → AlertTriangle · #FF7474
      User Story  → BookOpen      · #1FA191
      Test        → Aperture      · #FC964D

Run 'sync epics to plane' now to populate epics and stories from epics.md? [y/n]
```

If yes → proceed with SYNC_EPICS using this new project.

---

## SYNC_SPRINT

Bulk-update Plane states from `sprint-status.yaml` after `bmad-sprint-planning`.

Parse `development_status`. Skip `epic-N` and `epic-N-retrospective` keys. Process `N-M-*` keys as stories — derive story_id from first two segments.

Fetch all work items (paginate `mcp_plane_list_work_items` with `per_page=100`). Match by title lookup `"Story N.M"` in memory. Then call `mcp_plane_retrieve_work_item_by_identifier` with the matched `sequence_id` to get the full work item. ⚠️ Do NOT use `mcp_plane_search_work_items` — it returns empty results.

Only update items where current Plane state differs from target. Never halt on individual failures — collect and report all results.

---

## CREATE_PROJECT

Scaffold a new Plane project that mirrors the AutomaLead template: states, custom labels, work item types, and enabled features.

**Step 1 — Gather inputs:**
Ask the user for:

- `project_name`: Human-readable name (e.g. `MyApp`)
- `identifier`: Uppercase shortcode (auto-suggest from initials of name words, max 12 chars, e.g. `MYAPP`)

Resolve the invoking user's Plane member ID (see **Member ID Resolution**). This becomes `project_lead`.

Confirm before creating:

```
Will create Plane project:
  Name:       {project_name}
  Identifier: {IDENTIFIER}
  Lead:       {display_name}
Proceed? [y/n]
```

**Step 2 — Create project (with identifier collision handling):**

⚠️ **Plane enforces globally-unique identifiers across ALL workspace projects.** `HTTP 409 Conflict` means the identifier is taken.

**Identifier strategy:**
1. Try `identifier` (user's chosen value).
2. If 409: append digit → `{identifier}2`, `{identifier}3`, etc. (max 3 retries).
3. If all fail: fall back to initials of each word in `project_name`, uppercased, max 12 chars.
4. If STILL 409: ask user for a new identifier.

**⚠️ `is_time_tracking_enabled` causes 400 Bad Request** — Plane's API silently rejects it. Never pass this field.

Call `mcp_plane_create_project`:

- `name`: project_name
- `identifier`: IDENTIFIER (uppercase)
- `timezone`: `America/Sao_Paulo`
- `cycle_view`: true
- `is_issue_type_enabled`: true
- `project_lead`: invoking user's `plane_member_id`

Store the returned `project_id` and `identifier` for all subsequent steps.

**⚠️ Ambiguous matching alert:** If the user says "it created the project" after multiple 409s and retries with different identifiers, the project may exist under a retried identifier. Use `curl` to list all workspace projects and match by `name` case-insensitively to find the actual `project_id`:
```
curl -s "https://api.plane.so/api/v1/workspaces/{workspace_slug}/projects/" -H "x-api-key: {key}"
```

**Step 3 — Configure states:**
Fetch current states via `mcp_plane_list_states`. Upsert to match this exact set:

| Name             | Color     | Group     | Default |
| ---------------- | --------- | --------- | ------- |
| Backlog          | #d9d9d9 | backlog   | ✅      |
| Todo             | #3f76ff | unstarted |         |
| In Development   | #f59e0b | started   |         |
| In Review        | #f59e0b | started   |         |
| Ready for QA     | #16a34a | completed |         |
| Ready to Release | #16a34a | completed |         |
| Done             | #16a34a | completed |         |
| Blocked          | #dc2626 | cancelled |         |
| Cancelled        | #dc2626 | cancelled |         |

Rules:

- Match by name (case-insensitive). If found: update `color` and `group` if different.
- If not found: create with the specified values.
- For states auto-created by Plane that are NOT in the list above: delete them (only if they have 0 work items assigned — skip and warn otherwise).
- Set `default: true` only on Backlog.

**Step 4 — Create custom labels:**
Fetch existing labels via `mcp_plane_list_labels`. Create only those missing (case-insensitive name match):

| Name           | Color   |
| -------------- | ------- |
| frontend       | #9900ef |
| framework      | #def511 |
| backend        | #0693e3 |
| test           | #16a34a |
| blocked        | #ff6900 |
| feature        | #00ccff |
| bug            | #ff0000 |
| improvement    | #d6d6d6 |
| chore          | #d6d6d6 |
| incident       | #d6d6d6 |
| rollback       | #d6d6d6 |
| non-billable   | #d6d6d6 |
| project-management | #d6d6d6 |
| planning       | #d6d6d6 |
| meeting        | #d6d6d6 |
| technical      | #d6d6d6 |
| devops         | #d6d6d6 |
| pr-review      | #d6d6d6 |
| bmad-generated | #ff6900 |
| ai-planned     | #ff6900 |
| ai-spec        | #ff6900 |
| ai-implemented | #ff6900 |
| ai-rework      | #ff6900 |
| human-reviewed | #ff6900 |
| failed-test | #ff6900 |
| failed-test-2-plus | #ff6900 |

**Step 5 — Create work item types:**
Fetch existing types via `mcp_plane_list_work_item_types`. Create only those missing (case-insensitive name match):

⚠️ **Plane auto-creates a default `Task` type** with `is_default: true` on every new project. You MUST detect this and skip it.

**Fetch existing types:** GET `/workspaces/{slug}/projects/{id}/work-item-types/` via curl. The MCP `mcp_plane_list_work_item_types` tool is unreliable — use direct curl:
```
curl -s "https://api.plane.so/api/v1/workspaces/{slug}/projects/{id}/work-item-types/" -H "x-api-key: {key}"
```
Build a map of `name → {id, is_default}` from the response. The default Task has `"is_default": true` and often a description like `"Default work item type..."`.

Create only those missing from this list (case-insensitive name match, skipping items where `is_default: true` already fills the role):

| Name       | is_epic |
| ---------- | ------- |
| Task       | false   |
| Bug        | false   |
| User Story | false   |
| Test       | false   |

**Skip logic:**
- If `Task` exists with `is_default: true` → **skip** Task creation entirely. Use the default type's ID for property assignments.
- If `Task` exists but `is_default: false` (rare) → skip, use that ID.
- If any type name already exists (case-insensitive) → skip it.
- Only create types whose names are absent from the lookup.

> ⚠️ **Icon and color styling cannot be set via the Plane API.** After scaffolding, instruct the user to update these manually in **Project Settings → Work item types**:
>
> | Type       | Icon          | Color     |
> | ---------- | ------------- | --------- |
> | Task       | (default)     | `#6695FF` |
> | Bug        | AlertTriangle | `#FF7474` |
> | User Story | BookOpen      | `#1FA191` |
> | Test       | Aperture      | `#FC964D` |

**Step 6 — Create custom properties per work item type:**
For each work item type (using existing types from Step 5), create the following properties. **Always use the existing type's ID** — never create a duplicate type first.

Fetch existing properties first via curl GET `/work-item-types/{type_id}/work-item-properties/` and skip any whose `display_name` already matches (case-insensitive).

| Type       | Property       | property_type | settings                            |
| ---------- | -------------- | ------------- | ----------------------------------- |
| Task       | Deploy Date    | `DATETIME`    | `{"display_format":"dd/MM/yyyy"}`   |
| Task       | Affected Files | `TEXT`        | `{"display_format":"multi-line"}`   |
| Task       | Spec Link      | `TEXT`        | `{"display_format":"single-line"}`  |
| Bug        | Affected Files | `TEXT`        | `{"display_format":"multi-line"}`   |
| Bug        | Spec Link      | `TEXT`        | `{"display_format":"single-line"}`  |
| Bug        | Deploy Date    | `DATETIME`    | `{"display_format":"dd/MM/yyyy"}`   |
| User Story | Spec Link      | `TEXT`        | `{"display_format":"single-line"}`  |
| User Story | Deploy Date    | `DATETIME`    | `{"display_format":"dd/MM/yyyy"}`   |
| Test       | Spec Link      | `TEXT`        | `{"display_format":"single-line"}`  |
| Test       | Deploy Date    | `DATETIME`    | `{"display_format":"dd/MM/yyyy"}`   |

**Verification (after each type's properties are created):**
```
curl -s ".../work-item-types/{type_id}/work-item-properties/" -H "x-api-key: {key}" | grep -o '"display_name":"[^"]*"' | sort -u
```
Confirm all expected `display_name` values appear before moving to the next type.

---

## Member ID Resolution

Used by STORY_CREATED (when assigning).

Check `/memories/plane-profile.md` first — if `plane_member_id` exists, use it directly.

Otherwise ask for display name or email, call `mcp_plane_get_workspace_members`, match the member, and save to `/memories/plane-profile.md`:

```markdown
# Plane Profile

- **display_name**: {name}
- **email**: {email}
- **plane_member_id**: {uuid}
```

---

## Safety Rules

- **Never delete** epics or work items.
- **Never duplicate** — check existence before creating. Plane auto-creates a default Task; detect it via curl before attempting to create another.
- **Never change state** of existing items during SYNC_EPICS.
- **Confirm before bulk changes** (> 10 items).
- Always use `state=`, never `state_id=`.
- Always use `comment_html=`, never `data=`.
- If no Plane projects found: halt with `"No Plane projects found. Check MCP server config."`
- **HTTP 409 on create_project = identifier collision.** Retry with variant identifiers before giving up.
- **`is_time_tracking_enabled=true` → 400 pydantic error.** Never pass this field to `mcp_plane_create_project`.
- **DATETIME properties need settings:** `{"display_format":"dd/MM/yyyy"}`. Omitted settings → validation error.
- **MCP `Output validation error: None is not of type 'string'` is usually a false positive.** Verify via curl GET after creation.
- **When MCP tools for listing types/labels are unavailable**, use direct curl to the Plane REST API with the x-api-key header.
