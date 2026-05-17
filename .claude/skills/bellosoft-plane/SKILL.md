---
name: bellosoft-plane
description: "Keeps Plane tickets in sync across the full BMAD story lifecycle. Trigger after bmad-create-story, bmad-dev-story, or bmad-code-review completes, or when the user says 'update plane', 'plane', 'sync epics to plane', 'sync sprint to plane', or 'create plane project'."
---

# Plane Sync
Keeps every Plane ticket accurate across the full BMAD workflow — story creation, development, code review, and QA — with a single invocation model: say `"update plane"` (or just `"plane"`) and the right thing happens automatically.

**How it works:** Reads the current story file to infer which lifecycle event just completed, then applies the correct Plane state, assignment, description update, and comment. Bulk sync commands are also available.

**Lifecycle state machine:**

| After this BMAD skill completes | Plane state | Action |
|---|---|---|
| `bmad-create-story` | In Development | Assign to you |
| `bmad-dev-story` (in-progress or done) | In Development | Update description with Dev Agent Record |
| `bmad-code-review` | In Review | Run tests, add results comment, move to In Review |

Load `references/workflow.md` to begin.
