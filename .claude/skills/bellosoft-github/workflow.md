# GitHub Flow Workflow

Creates Plane-compatible git branches, conventional commits, and pull requests.
All Plane lookups go through Plane MCP. All git/GitHub commands run in the terminal.

---

## Setup

**Config:** Load from `{project-root}/_bmad/bmm/config.yaml`:
- `project_name` — used to auto-select the Plane project
- `implementation_artifacts` — story files location

**Project resolution:** Call `mcp_plane_list_projects`. Match `project_name` case-insensitively to find `project_id` and `identifier` (e.g. `NOKEY`). Store both.

**Sprint status:** Read `docs/implementation-artifacts/sprint-status.yaml` to get `project_key` as a fallback identifier if Plane lookup fails.

---

## Command Routing

| What the user says | Command |
|---|---|
| `create branch` / `github branch` / `branch for story [id]` | GITHUB_BRANCH |
| `commit` / `git commit` / `commit changes` | GITHUB_COMMIT |
| `create pr` / `open pr` / `github pr` / `pull request` | GITHUB_PR |

---

## Shared: Resolve Plane Ticket ID

Every command needs `{ticket_id}` (e.g. `NOKEY-42`). Run this resolution once per session:

1. Identify the target story — from user-provided ID, or most recently modified `.md` in `implementation_artifacts`.
2. Read the story file. Extract `story_id` (from frontmatter `story_id:`) and `title`.
3. **If current branch follows `{type}/{identifier}-{sequence_id}-{slug}` pattern** (e.g. `feature/AUTOMALEAD-14-...`), parse `sequence_id` directly from the branch name — skip to step 5.
4. **Otherwise:** call `mcp_plane_list_work_items` with `project_id` + `per_page=100`. Filter results in memory: find the item whose `name` contains `Story {story_id}` (case-insensitive). Extract `sequence_id`.
   - ⚠️ Do NOT use `mcp_plane_search_work_items` — it returns empty results and is unreliable.
5. Call `mcp_plane_retrieve_work_item_by_identifier` with `issue_identifier={sequence_id}` (integer) and `project_identifier={project.identifier}` (e.g. `AUTOMALEAD`). This is the **only reliable lookup method**.
6. Compose `ticket_id = "{project.identifier}-{sequence_id}"` (e.g. `NOKEY-42`).
7. If no match found: halt and output:
   ```
   ⚠️  No Plane ticket found for Story {story_id}.
   Run 'sync epics to plane' first, then retry.
   ```

---

## GITHUB_BRANCH

Creates a Plane-compatible git branch for the current story.

### Step 1 — Resolve ticket ID
Run **Resolve Plane Ticket ID** above.

### Step 2 — Determine branch type
Infer from the story title or ask the user:

| Story characteristics | Branch type |
|---|---|
| New feature / implementation | `feature` |
| Bug fix | `fix` |
| Refactor, cleanup, migration | `chore` |
| Documentation only | `docs` |
| Security hardening, infra | `feature` (default) |

### Step 3 — Build branch name
- Take the story title, lowercase it, replace spaces/special chars with `-`, collapse consecutive `-`, strip trailing `-`.
- Truncate the slug to **40 characters** maximum.
- Final name: `{type}/{ticket_id}-{slug}`
- Example: `feature/NOKEY-42-security-hardening-encryption-tenant-isolation`

### Step 4 — Ensure clean base
Run:
```bash
git status
```
If working tree is dirty: warn the user and ask whether to stash (`git stash`) or abort.

Check current branch:
```bash
git branch --show-current
```
If not on `main` or `develop`, warn the user and ask whether to switch first.

### Step 5 — Create branch
```bash
git checkout -b {branch_name}
```

If the branch already exists, append a short suffix like `-2` and retry once, then halt if still failing.

### Step 6 — Report
```
✅ Branch created: {branch_name}
   Plane ticket: {ticket_id} — {story_title}

Next step: implement the story, then run 'commit' to push your changes.
```

---

## GITHUB_COMMIT

Stages and commits all current changes with a Plane-linked conventional commit message.

### Step 1 — Resolve ticket ID
Extract from current branch name if possible:
```bash
git branch --show-current
```
Parse `{ticket_id}` from branch name pattern `{type}/{ticket_id}-*`. If the branch name does not follow the convention, run **Resolve Plane Ticket ID** from Plane.

### Step 2 — Check for changes
```bash
git status --short
```
If working tree is clean: output `Nothing to commit — working tree clean.` and halt.

Show the list of changed files to the user.

### Step 3 — Determine commit type
Ask the user to choose (or infer from changed files if obvious):

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `chore` | Build, config, dependency, tooling changes |
| `docs` | Documentation only |
| `refactor` | Structural change with no new feature |
| `test` | Adding or fixing tests only |
| `security` | Security hardening (use when story is security-focused) |

### Step 4 — Get commit description
Ask: `Short description (imperative, ≤72 chars total):`
Validate: total length of `{type}({ticket_id}): {description}` must be ≤ 72 characters.

### Step 5 — Stage and commit
```bash
git add -A
git commit -m "{type}({ticket_id}): {description}"
```

If the commit fails (pre-commit hook, lint error, etc.): show the error output and halt. Do NOT retry blindly.

### Step 6 — Offer to push
Ask: `Push to remote? [y/n]`
If yes:
```bash
git push --set-upstream origin {branch_name}
```
Output the remote URL for the branch if available.

### Step 7 — Report
```
✅ Committed: {type}({ticket_id}): {description}
   Files staged: {count}
   Branch: {branch_name}
   {pushed to remote or "Not pushed yet — run 'git push' when ready"}
```

---

## GITHUB_PR

Creates a GitHub pull request with Plane state automation wired up via the `[ticket_id]` bracket format.

**Prerequisite:** `gh` CLI must be installed and authenticated. Check: `gh auth status`. If not authenticated, halt:
```
⚠️  GitHub CLI not authenticated. Run: gh auth login
```

### Step 1 — Resolve ticket ID and story context
Extract `ticket_id` from current branch name. Read story file for `title` and `story_id`.

### Step 2 — Verify branch is pushed
```bash
git status -sb
```
If branch has no remote tracking, push first:
```bash
git push --set-upstream origin {branch_name}
```

### Step 3 — Determine PR title
Format: `[{ticket_id}] {story_title}`
Example: `[NOKEY-42] Security Hardening — Encryption, Tenant Isolation & Hangfire Auth`

The `[{ticket_id}]` prefix (with brackets) activates **Plane state automation** — when this PR is merged, Plane will automatically move the work item to the state mapped to "PR merged" in your project's PR state mapping.

### Step 4 — Build PR body
Compose the PR description automatically from the story file:

```markdown
## Summary

{story user story paragraph — the "As a / I want / So that" block}

## Plane Work Item

[{ticket_id}](https://app.plane.so/) — {story_title}

## Acceptance Criteria

{AC list from the story file, rendered as checkboxes}

## Files Changed

{key files from the story's File List section, or leave placeholder}

## Testing

- [ ] `dotnet build` — zero errors
- [ ] All existing tests pass
- [ ] Acceptance criteria manually verified
```

Show the draft to the user and ask: `Open PR with this description? [y/n/edit]`
- `y` → proceed
- `n` → abort
- `edit` → ask user to provide a replacement body

### Step 5 — Create PR
```bash
gh pr create \
  --title "{pr_title}" \
  --body "{pr_body}" \
  --base main
```

If the repo uses `develop` as the base branch instead of `main`, substitute accordingly. Check:
```bash
git remote show origin | grep "HEAD branch"
```

### Step 6 — Report
```
✅ PR created: {pr_url}
   Title: {pr_title}
   Plane ticket: {ticket_id} — {story_title}
   State automation: ACTIVE — merging this PR will auto-update the Plane work item.

Next steps:
  • Request review from teammates
  • Run 'plane' to sync story status to 'In Review' in Plane
```

---

## Error Handling

| Error | Recovery |
|---|---|
| Plane ticket not found | Halt — "Run 'sync epics to plane' first" |
| Branch already exists | Suggest incremental suffix or abort |
| Pre-commit hook fails | Show error, halt — do not bypass hooks |
| `gh` CLI not installed | Halt with install instructions |
| `gh` not authenticated | Halt with `gh auth login` instruction |
| Dirty working tree at branch create | Offer stash or abort |
| Push fails (remote conflict) | Show error — never force-push without explicit user consent |

---

## Safety Rules

- **Never force-push** (`--force`) without explicit user confirmation.
- **Never bypass pre-commit hooks** (`--no-verify`).
- **Always use brackets** `[ticket_id]` in PR titles to enable Plane state automation.
- **Never commit secrets** — if `git status` shows `.env`, `appsettings.*.json` with real keys, warn and halt.
