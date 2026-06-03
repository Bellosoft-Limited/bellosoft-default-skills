# Shared Tracker Bootstrap — bellosoft

**Load this block whenever a skill is about to push/read from a tracker for the first time.**

This runs once per project. After the choice is saved to `docs/plan/status.md`, skip this block entirely on subsequent calls.

---

## When to run

Run this bootstrap BEFORE any tracker push/pull operation when `docs/plan/status.md` does NOT contain a `tracker:` line (or the file doesn't exist).

---

## Bootstrap flow

### Step B1 — Check saved preference

Read `docs/plan/status.md`. Look for:
```
tracker: jira
```
or
```
tracker: plane
```

If found → use that tracker, skip to Step B4. Do not ask again.

---

### Step B2 — Auto-detect available MCPs

Probe silently (do not show errors to user):
1. Try `mcp__atlassian__jira_get_myself()` → set `jira_available = true` if succeeds
2. Try `mcp_plane_list_projects()` → set `plane_available = true` if succeeds

---

### Step B3 — Ask (only if needed)

**Both available:**
```
Two trackers are connected. Which would you like to use for this project?
  1. Jira
  2. Plane
  3. No tracker — give me markdown I'll create tickets manually
```

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

**Neither:**
```
⚠️ No tracker connected.

Options:
  1. Continue with markdown only — I'll create tickets manually
  2. I'll connect a tracker now — run /bellosoft-jira setup or /bellosoft-plane setup
```
→ If user picks 1, set `tracker: none` and proceed.
→ If user picks 2, stop here and wait for user to set up tracker.

---

### Step B4 — Project selection

**Jira path:**
1. Check `docs/plan/jira-profile.md` for `project_key:` — if found, confirm: `"Using Jira project {KEY}. Correct? [y/n]"`
2. If not found or user says no → call `mcp__atlassian__jira_get_all_projects()` and list
3. User picks project OR:
   ```
   Don't have a Jira project yet?
     → Type "create" to scaffold a new one
   ```
4. If "create" → delegate to `/bellosoft-jira setup` CREATE_PROJECT flow
5. Save `project_key` to `docs/plan/jira-profile.md`

**Plane path:**
1. Check `docs/plan/status.md` for `plane_project_id:` — if found, confirm silently
2. If not found → call `mcp_plane_list_projects()` and list
3. User picks project OR:
   ```
   Don't have a Plane project yet?
     → Type "create" to scaffold a new one
   ```
4. If "create" → delegate to `/bellosoft-plane setup` (CREATE_PROJECT command)
5. Save `plane_project_id` and `project_identifier` to `docs/plan/status.md`

---

### Step B5 — Save and proceed

Append/update `docs/plan/status.md`:
```markdown
tracker: jira          # or plane, or none
jira_project_key: PROJ # jira only
plane_project_id: ...  # plane only
```

Then continue with the calling skill's normal flow.

---

## Quick reference for calling skills

In any skill that needs tracker access, add this step:

```
## Step N — Tracker resolution (first-time only)
Load and follow `references/tracker-bootstrap.md`.
Skip if `docs/plan/status.md` already contains `tracker:`.
```

The bootstrap is in the bellosoft-plane skill folder but is shared — all bellosoft
skills can reference it as a known location:
`.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`
