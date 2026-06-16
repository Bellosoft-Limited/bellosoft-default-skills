# Next-Gen Jira Quirks

**For discovery, ADF, sub-task rules, labels, error handling: see `jql-guide.md`.**

---

## REST Endpoint Quirk

Next-gen instances may not expose `/rest/api/3/issues`.

**Use `/rest/api/2/issue` as fallback** when MCP unavailable.

---

## Story Points Field Availability

Next-gen projects may not expose story points for all issue types (e.g., Bug, Task).

**Rule:** Always set both when discovered in createmeta (see `jql-guide.md` → "Custom Field IDs"):
- Story points field (if available in this issue type)
- `timetracking.originalEstimate` (always)

If story points unavailable for this issue type, timetracking alone is sufficient.

---

## Known Instances

### belloprojects.atlassian.net (AP project)
- Story Points: **Not available** in Bug/Task/Feature types
- Use `/rest/api/2/issue` endpoint (v3 returns 404)
- Sub-task type: 10012 (verify via createmeta)
- Always set `timetracking.originalEstimate` on bugs
