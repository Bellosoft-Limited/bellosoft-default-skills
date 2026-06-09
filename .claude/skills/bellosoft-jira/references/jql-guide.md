# Jira API Reference — bellosoft-jira

Battle-tested patterns for the Atlassian MCP (`mcp__atlassian`) and Jira REST API.
Load this file at the start of every bellosoft-jira invocation.

---

## MCP Tool Names

| Operation | MCP Tool |
|-----------|----------|
| Get current user | `mcp__atlassian__jira_get_myself` |
| List projects | `mcp__atlassian__jira_get_all_projects` |
| Get issue types | `mcp__atlassian__jira_get_issue_types` |
| Get all fields | `mcp__atlassian__jira_get_fields` |
| Create issue | `mcp__atlassian__jira_create_issue` |
| Get issue | `mcp__atlassian__jira_get_issue` |
| Update issue | `mcp__atlassian__jira_update_issue` |
| Search issues | `mcp__atlassian__jira_search` |
| Get transitions | `mcp__atlassian__jira_get_issue_transitions` |
| Transition issue | `mcp__atlassian__jira_transition_issue` |
| Add comment | `mcp__atlassian__jira_add_comment` |
| Create sprint | `mcp__atlassian__jira_create_sprint` (may not be available) |

---

## ADF (Atlassian Document Format)

All description and comment fields require ADF — never pass plain strings.

### Minimal paragraph
```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [{ "type": "text", "text": "Your text here." }]
    }
  ]
}
```

### Heading
```json
{
  "type": "heading",
  "attrs": { "level": 3 },
  "content": [{ "type": "text", "text": "Acceptance Criteria" }]
}
```

### Bullet list
```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "First item" }] }
      ]
    },
    {
      "type": "listItem",
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "Second item" }] }
      ]
    }
  ]
}
```

### Bold / italic marks
```json
{ "type": "text", "text": "Bold text", "marks": [{ "type": "strong" }] }
{ "type": "text", "text": "Italic text", "marks": [{ "type": "em" }] }
{ "type": "text", "text": "Code", "marks": [{ "type": "code" }] }
```

### Full story template (user story + ACs)
```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "As a ", "marks": [{"type": "strong"}] },
        { "type": "text", "text": "{persona}" },
        { "type": "text", "text": ", I want to ", "marks": [{"type": "strong"}] },
        { "type": "text", "text": "{action}" },
        { "type": "text", "text": " so that ", "marks": [{"type": "strong"}] },
        { "type": "text", "text": "{outcome}." }
      ]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "Acceptance Criteria" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "{AC1}" }] }]
        }
      ]
    }
  ]
}
```

---

## Custom Field IDs

**Never hardcode these — always discover via `jira_get_fields()` and cache in `docs/planning-artifacts/jira-profile.md`.**

Common field names to search for:

| Purpose | Common field name(s) |
|---------|---------------------|
| Story points | "Story Points", "Story point estimate" |
| Sprint | "Sprint" |
| Epic link (classic) | "Epic Link" |
| Epic name (classic) | "Epic Name" |
| Original estimate | "Original Estimate" |

### Field discovery pattern
```
fields = mcp__atlassian__jira_get_fields()
story_points_field = first field where name in ["Story Points", "Story point estimate"]
sprint_field = first field where name == "Sprint"
```

Typical IDs (vary per instance — always verify):
- `customfield_10058` — Story Points (Jira Software classic)
- `customfield_10016` — Story point estimate (next-gen)
- `customfield_10020` — Sprint
- `customfield_10014` — Epic Link (classic only)
- `customfield_10011` — Epic Name (classic only)

---

## Project Types

### Next-gen (team-managed)
- Epics are standard issues with type "Epic"
- Stories link to epics via `parent` field: `{ "parent": { "key": "PROJ-5" } }`
- Sub-tasks use `parent` field pointing to story key
- No `customfield_10014` (Epic Link)

### Classic (company-managed)
- Epics use type "Epic" + `customfield_10011` (Epic Name) must be set
- Stories link to epics via `customfield_10014` = epic key string
- Sub-tasks require parent field + "Sub-task" issue type
- Hierarchy: Epic → Story → Sub-task (three levels)

### Detection
```
result = jira_search(jql="project={KEY} AND issuetype=Epic ORDER BY created ASC", max_results=1)
if result.issues[0].fields.parent exists → next-gen
else → classic (check for customfield_10014)
```

---

## JQL Patterns

### Active sprint issues
```
project = PROJ AND sprint in openSprints() ORDER BY priority DESC
```

### My active sprint issues
```
assignee = currentUser() AND sprint in openSprints() AND project = PROJ
```

### Epic stories
```
project = PROJ AND issuetype = Story AND parent = PROJ-5
```

### All issues by label
```
project = PROJ AND labels = "ai-generated"
```

### Epics only
```
project = PROJ AND issuetype = Epic ORDER BY created ASC
```

### Issues updated since date
```
project = PROJ AND updated >= "2026-01-01"
```

### Blocked issues
```
project = PROJ AND labels = Blocked AND sprint in openSprints()
```

### Pagination
```
mcp__atlassian__jira_search(jql=..., max_results=100, start_at=0)
```
Increment `start_at` by `max_results` until `start_at >= total`.

---

## Transition Patterns

Never hardcode transition IDs — they vary per project workflow.

```
transitions = mcp__atlassian__jira_get_issue_transitions(issue_key)
# returns list: [{ id: "11", name: "To Do" }, { id: "21", name: "In Progress" }, ...]

target = first transition where name.lower().contains(status_name.lower())
mcp__atlassian__jira_transition_issue(issue_key, transition_id=target.id)
```

Common transition names (vary by workflow):
- "To Do" / "Backlog"
- "In Progress" / "In Development"
- "In Review" / "Code Review"
- "Done" / "Closed" / "Resolved"

---

## Sprint Operations

Sprint IDs are integers. Always store the ID, not the name.

### Assign issue to sprint
```
mcp__atlassian__jira_update_issue(
  issue_key = "PROJ-42",
  fields = { "customfield_10020": {sprint_id_integer} }
)
```

### Sprint creation (REST fallback if MCP unavailable)
```bash
curl -s -X POST \
  "{JIRA_URL}/rest/agile/1.0/sprint" \
  -u "{JIRA_USERNAME}:{JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sprint 3",
    "startDate": "2026-06-10T00:00:00.000Z",
    "endDate": "2026-06-24T00:00:00.000Z",
    "originBoardId": 42
  }'
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Field 'description' requires ADF` | Passed plain string | Wrap in ADF doc object |
| `400 Bad Request` on sub-task create | Sent `timetracking` or story-points — not available on Sub-tasks | Remove both fields; put estimate in description text only |
| `400 Bad Request` on sub-task description | Jira create-meta reports `type: string` but API requires ADF | Always use ADF for description, even when meta says string |
| `customfield_10014 is not on screen` | Wrong project type | Use `parent` field for next-gen |
| `Issue type 'Sub-task' not found` | Classic project, wrong name | Use `jira_get_issue_types` to find exact name |
| `Parent issue type is not valid` | Sub-task parent must be Story/Task | Check parent issue type |
| `Sprint X does not exist` | Used sprint name not ID | Use integer sprint ID from `jira_create_sprint` response |
| `Field 'story_points' is not valid` | Wrong field key | Discover via `jira_get_fields` |
| `Transition not found` | Hardcoded transition ID | Always fetch from `jira_get_issue_transitions` |

---

## Status Mapping (bellosoft → Jira)

| bellosoft status | Jira transition name |
|-----------------|---------------------|
| Backlog | "To Do" or "Backlog" |
| In Development | "In Progress" |
| In Review | "In Review" or "Code Review" |
| Done | "Done" or "Closed" |
| Blocked | add label "Blocked" (no transition) |

---

## Bellosoft-generated Label

All issues created by bellosoft skills must have:
```json
{ "labels": ["ai-generated"] }
```

This enables safe re-sync detection:
```
jql = "project = {KEY} AND labels = ai-generated"
```

---

## Issue Hierarchy Reference

```
Epic (type: Epic)
  └── Story (type: Story, links to epic via parent or customfield_10014)
        └── Sub-task (type: Sub-task, parent = story key)

Standalone Task (type: Task, no parent)
  └── Sub-task (type: Sub-task, parent = task key)
```

Area tags map to labels:
- `[BE]` → label: "backend"
- `[FE]` → label: "frontend"
- `[DB]` → label: "database"
- `[QA]` → label: "qa"
- `[INFRA]` → label: "infra"
- `[DEVOPS]` → label: "devops"
- `[MOB]` → label: "mobile"
- `[FW]` → label: "fullstack"
