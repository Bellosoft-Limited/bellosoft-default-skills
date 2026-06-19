# OpenProject API Guide — bellosoft reference

This file contains OpenProject API patterns, quirks, and field mappings.
Loaded by `bellosoft-openproject` at the start of every operation.

---

## Authentication

OpenProject uses **Bearer token** auth. Tokens are created at:
`My Account → Access Tokens → Add access token`

```bash
# Bearer (recommended):
curl -H "Authorization: Bearer $OP_TOKEN" https://{instance}/api/v3/users/me

# Basic auth alternative (username is the literal string "apikey"):
curl -u "apikey:$OP_TOKEN" https://{instance}/api/v3/users/me
```

**Required headers for ALL requests:**
```
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/hal+json
```

---

## Base URL

```
https://{instance}/api/v3/{resource}
```

`{instance}` is the full domain, e.g. `myorg.openproject.com` or `openproject.mycompany.internal`.

All responses are **HAL+JSON** — resources return `_type`, `_links`, and `_embedded` meta keys.
Related resources and allowed actions are referenced via `_links`, not field IDs.

---

## Work Packages

Work packages are OpenProject's issues/tickets. Epics, stories, tasks, and bugs are all work packages — differentiated by `type`.

### Key fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Auto-assigned |
| `subject` | string | The title |
| `description` | Formattable | `{"format":"markdown","raw":"...","html":"..."}` |
| `estimatedTime` | duration | ISO 8601: `"PT5H"` = 5 hours, `"PT1H30M"` = 1.5h |
| `storyPoints` | integer | Requires Backlogs plugin |
| `startDate` | date | `"YYYY-MM-DD"` |
| `dueDate` | date | `"YYYY-MM-DD"` |
| `percentageDone` | integer | 0–100 |
| `lockVersion` | integer | Required on PATCH for optimistic locking |

### Key links (set via `_links` in request body)

| Link | Meaning | Example href |
|------|---------|--------------|
| `type` | Work package type | `/api/v3/types/1` |
| `status` | Current status | `/api/v3/statuses/3` |
| `version` | Sprint / iteration | `/api/v3/versions/42` |
| `assignee` | Assigned user | `/api/v3/users/33` |
| `parent` | Parent work package | `/api/v3/work_packages/100` |
| `project` | Owning project | `/api/v3/projects/5` |

### Endpoints

```
GET    /api/v3/projects/{projectId}/work_packages   ← list for project (filterable)
POST   /api/v3/projects/{projectId}/work_packages   ← create in project
GET    /api/v3/work_packages/{id}                   ← get single
PATCH  /api/v3/work_packages/{id}                   ← update (include lockVersion)
GET    /api/v3/work_packages                        ← list all (cross-project, filterable)
```

### Create work package — minimal body

```json
{
  "subject": "My task",
  "description": { "format": "markdown", "raw": "## Details\n..." },
  "estimatedTime": "PT4H",
  "_links": {
    "type":    { "href": "/api/v3/types/1" },
    "status":  { "href": "/api/v3/statuses/1" },
    "version": { "href": "/api/v3/versions/42" },
    "assignee":{ "href": "/api/v3/users/33" },
    "parent":  { "href": "/api/v3/work_packages/100" }
  }
}
```

### Update work package — always include lockVersion

```bash
# Step 1: GET to fetch lockVersion
curl -s -H "Authorization: Bearer $OP_TOKEN" \
  "$OP_URL/api/v3/work_packages/{id}" > /tmp/op_wp.json
# Read lockVersion from JSON

# Step 2: PATCH with lockVersion
curl -s -X PATCH \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/{id}" \
  -d '{"lockVersion": 3, "_links": {"status": {"href": "/api/v3/statuses/5"}}}'
```

⚠️ **PATCH without `lockVersion` returns 409 Conflict.**

### Filter syntax

`filters` param is URL-encoded JSON array:
```json
[
  { "status":   { "operator": "=",  "values": ["1","2"] } },
  { "type":     { "operator": "=",  "values": ["3"] } },
  { "version":  { "operator": "=",  "values": ["42"] } },
  { "assignee": { "operator": "=",  "values": ["me"] } }
]
```

Common operators: `=` equals, `!` not equals, `~` contains, `o` open, `c` closed.

**Assignee value `"me"` uses the current authenticated user** — no need to resolve user ID for self-filtering.

Example list sprint issues:
```bash
FILTERS='[{"version":{"operator":"=","values":["42"]}},{"status":{"operator":"o","values":[]}}]'
curl -s -G "$OP_URL/api/v3/projects/$PROJECT_ID/work_packages" \
  --data-urlencode "filters=$FILTERS" \
  --data-urlencode 'pageSize=100' \
  -H "Authorization: Bearer $OP_TOKEN" > /tmp/op_sprint.json
cat /tmp/op_sprint.json
```

---

## Types

Types determine the work package category (Epic, Story, Task, Bug). Types are **project-configurable** — the IDs differ between OpenProject instances.

**Always resolve types at setup — never hardcode IDs.**

```
GET /api/v3/projects/{id}/types
```

Response: `_embedded.elements` — each has `id`, `name`, `color`, `isMilestone`.

Map names to IDs and save to `docs/planning-artifacts/openproject-profile.md`:
- Look for type with name matching "Epic" (case-insensitive)
- Look for type with name matching "Story" or "User Story"
- Look for type with name matching "Task" (usually the default)
- Look for type with name matching "Bug"

If "Epic" type doesn't exist, use parent/child nesting at the Story level — parent Story = pseudo-epic.

---

## Statuses

Statuses represent workflow states. Always fetched at setup — IDs differ per instance.

```
GET /api/v3/statuses
```

Response: `_embedded.elements` — each has `id`, `name`, `isClosed`, `isDefault`.

Map by name and save to profile:
- Default / New → starting state for new work packages
- In Progress (or equivalent)
- In Review / Code Review
- Done / Closed

---

## Versions (Sprints)

Versions are OpenProject's sprints/iterations.

```
GET  /api/v3/projects/{id}/versions    ← list for project
GET  /api/v3/versions                  ← list all (use filters)
POST /api/v3/versions                  ← create sprint
PATCH /api/v3/versions/{id}            ← update
```

### Create version (sprint)

```json
{
  "name": "Sprint 1",
  "description": { "format": "markdown", "raw": "First sprint" },
  "startDate": "2026-07-01",
  "endDate": "2026-07-14",
  "status": "open",
  "_links": {
    "definingProject": { "href": "/api/v3/projects/5" }
  }
}
```

`status`: `"open"` | `"locked"` | `"closed"`

### Assign WP to version

Include in create/update body:
```json
{ "_links": { "version": { "href": "/api/v3/versions/42" } } }
```

---

## Comments / Activities

```
GET  /api/v3/work_packages/{id}/activities   ← list journal entries + comments
POST /api/v3/work_packages/{id}/activities   ← add comment
PATCH /api/v3/activities/{id}                ← edit comment
```

### Add comment

```bash
curl -s -X POST \
  -H "Authorization: Bearer $OP_TOKEN" \
  -H "Content-Type: application/json" \
  "$OP_URL/api/v3/work_packages/{id}/activities" \
  -d '{"comment": {"raw": "This is a markdown **comment**."}}'
```

---

## Users

```
GET /api/v3/users/me                ← current user (id, login, name, email)
GET /api/v3/users/{id}              ← single user
GET /api/v3/users?filters=...       ← list / search users
GET /api/v3/memberships?filters=... ← list project members
```

Filter members by project:
```bash
FILTERS='[{"project":{"operator":"=","values":["5"]}}]'
curl -s -G "$OP_URL/api/v3/memberships" \
  --data-urlencode "filters=$FILTERS" \
  -H "Authorization: Bearer $OP_TOKEN"
```

---

## Projects

```
GET  /api/v3/projects        ← list (filterable by active, name, id, parent_id)
GET  /api/v3/projects/{id}   ← single project
POST /api/v3/projects        ← create
```

### Create project

```json
{
  "name": "My Project",
  "identifier": "my-project",
  "description": { "format": "markdown", "raw": "Project description" },
  "public": false
}
```

`identifier` must be globally unique, lowercase, hyphens only.

---

## Common API Gotchas

| Gotcha | ❌ Wrong | ✅ Correct |
|--------|---------|-----------|
| PATCH without lock | `PATCH {body}` | `PATCH {lockVersion: N, ...body}` |
| Status by name | `"status": "In Progress"` | `"_links": {"status": {"href": "/api/v3/statuses/3"}}` |
| Assignee by name | `"assignee": "John"` | `"_links": {"assignee": {"href": "/api/v3/users/33"}}` |
| Hardcode type ID | `"type": 1` | Fetch from `/api/v3/projects/{id}/types`, save to profile |
| Hardcode status ID | `"status": 5` | Fetch from `/api/v3/statuses`, save to profile |
| Pipe to jq | `curl ... \| jq .` | Write to temp file, then `cat` it |

---

## Temp-file pattern (no jq required)

```bash
OP_URL=$(cat .secrets/op-url.txt | tr -d '\n')
OP_TOKEN=$(cat .secrets/op-api-token.txt | tr -d '\n')
curl -s -H "Authorization: Bearer $OP_TOKEN" -H "Accept: application/hal+json" \
  "$OP_URL/api/v3/work_packages/{id}" > /tmp/op_result.json
cat /tmp/op_result.json
```

Read the raw JSON from the file. Parse it directly — no external tools needed.

---

## Label conventions (tags in work package subjects / custom fields)

OpenProject doesn't have a native label-based tag system per se — tags are via categories or custom fields.

For bellosoft area tags, embed the tag in the work package `subject`:
```
E8-S2-T1 [BE] Add campaign scheduling method
```

This mirrors the Jira/Plane approach and makes tags visible in the board without custom field setup.

---

## Pagination

All collection responses:
- `total` — total count of items
- `count` — items in this page
- `pageSize` — requested page size
- `offset` — 1-based current offset
- `_links.nextByOffset` — URL template for next page

Always paginate: use `pageSize=100` and iterate until `count < pageSize`.

