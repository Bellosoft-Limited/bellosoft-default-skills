# Shared Tracker Bootstrap — bellosoft

**Load this block whenever a skill is about to push/read from a tracker for the first time.**

This runs once per project. After the choice is saved to `docs/planning-artifacts/status.md`, skip this block entirely on subsequent calls.

---

## When to run

Run this bootstrap BEFORE any tracker push/pull operation when `docs/planning-artifacts/status.md` does NOT contain a `tracker:` line (or the file doesn't exist).

---

## Bootstrap flow

### Step B1 — Check saved preference

Read `docs/planning-artifacts/status.md`. Look for:
```
tracker: jira
```
or
```
tracker: plane
```
or
```
tracker: openproject
```

If found → use that tracker, skip to Step B4. Do not ask again.

---

### Step B2 — Auto-detect available trackers

**MCP check** (probe silently — do not show errors to user):
1. Try `mcp__atlassian__jira_get_myself()` → set `jira_available = true` if succeeds
2. Try `mcp_plane_list_projects()` → set `plane_available = true` if succeeds

**REST check for OpenProject:**
3. Check if `.secrets/op-url.txt` and `.secrets/op-api-token.txt` exist:
```bash
test -f .secrets/op-url.txt && test -f .secrets/op-api-token.txt && echo "op_available=true"
```
If both files exist → set `op_available = true`.

---

### Step B3 — Ask (only if needed)

**All three available:**
```
Multiple trackers are configured. Which would you like to use for this project?
  1. Jira
  2. Plane
  3. OpenProject
  4. No tracker — give me markdown I'll create tickets manually
```

**Two available:** list those two plus "No tracker".

**Only Jira:**
```
Jira is connected. Use Jira for this project? [y/n]
(n → markdown-only mode)
```

**Only Plane:**
```
Plane is connected. Use Plane for this project? [y/n]
(n → markdown-only mode)
```

**Only OpenProject:**
```
OpenProject credentials found. Use OpenProject for this project? [y/n]
(n → markdown-only mode)
```

**None:**
```
⚠️ No tracker connected.

Options:
  1. Continue with markdown only — I'll create tickets manually
  2. Set up Jira    → run /bellosoft-jira setup
  3. Set up Plane   → run /bellosoft-plane setup
  4. Set up OpenProject → run /bellosoft-openproject setup
```
→ If user picks 1, set `tracker: none` and proceed.
→ If user picks 2/3/4, stop here and wait for user to set up their tracker.

---

### Step B4 — Project selection

**Jira path:**
1. Check `docs/planning-artifacts/jira-profile.md` for `project_key:` — if found, confirm: `"Using Jira project {KEY}. Correct? [y/n]"`
2. If not found or user says no → call `mcp__atlassian__jira_get_all_projects()` and list
3. User picks project OR:
   ```
   Don't have a Jira project yet?
     → Type "create" to scaffold a new one
   ```
4. If "create" → delegate to `/bellosoft-jira setup` CREATE_PROJECT flow
5. Save `project_key` to `docs/planning-artifacts/jira-profile.md`

**Plane path:**
1. Check `docs/planning-artifacts/status.md` for `plane_project_id:` — if found, confirm silently
2. If not found → call `mcp_plane_list_projects()` and list
3. User picks project OR:
   ```
   Don't have a Plane project yet?
     → Type "create" to scaffold a new one
   ```
4. If "create" → delegate to `/bellosoft-plane setup` (CREATE_PROJECT command)
5. Save `plane_project_id` and `project_identifier` to `docs/planning-artifacts/status.md`

**OpenProject path:**
1. Check `docs/planning-artifacts/openproject-profile.md` for `project_id:` — if found, confirm: `"Using OpenProject project {name} (id: {id}). Correct? [y/n]"`
2. If not found → list projects via REST:
   ```bash
   curl -s -H "Authorization: Bearer $(cat .secrets/op-api-token.txt | tr -d '\n')" \
     "$(cat .secrets/op-url.txt | tr -d '\n')/api/v3/projects" > /tmp/op_projects.json
   cat /tmp/op_projects.json
   ```
3. User picks project OR:
   ```
   Don't have an OpenProject project yet?
     → Type "create" to scaffold a new one
   ```
4. If "create" → delegate to `/bellosoft-openproject setup` CREATE_PROJECT flow
5. Save `op_project_id` and `op_project_identifier` to `docs/planning-artifacts/status.md`

---

### Step B5 — Save and proceed

Append/update `docs/planning-artifacts/status.md`:
```markdown
tracker: jira           # or plane, openproject, or none
jira_project_key: PROJ  # jira only
plane_project_id: ...   # plane only
op_project_id: 5        # openproject only
op_project_identifier: my-project  # openproject only
```

Then continue with the calling skill's normal flow.

---

## Quick reference for calling skills

In any skill that needs tracker access, add this step:

```
## Step N — Tracker resolution (first-time only)
Load and follow `references/tracker-bootstrap.md`.
Skip if `docs/planning-artifacts/status.md` already contains `tracker:`.
```

The bootstrap is in the bellosoft-plane skill folder but is shared — all bellosoft
skills can reference it as a known location:
`.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`
