---
name: bellosoft-github
description: >
  Creates git branches, conventional commits, and pull requests following bellosoft
  conventions. Supports Jira and Plane ticket IDs, or works without any tracker.
  Triggers: "create branch", "branch for story [id]", "commit", "create PR",
  "open PR", "github branch", "github commit", "github pr", "pull request".
---

# Skill: bellosoft-github

Git workflow layer for the bellosoft ecosystem. Handles branching, committing,
and PR creation with automatic tracker linking.

```
/bellosoft-github branch    ← create branch for current story/ticket
/bellosoft-github commit    ← stage and commit with conventional message
/bellosoft-github pr        ← open a pull request with tracker automation
```

---

## Ticket ID resolution

Every command needs a `{ticket_id}`. Resolve in this order:

1. **User provided** — e.g. `/bellosoft-github branch PROJ-42`
2. **Current branch name** — parse `{type}/{ticket_id}-{slug}` pattern
3. **Tracker lookup** — read `docs/planning-artifacts/status.md` for `tracker:` then:
   - `tracker: jira` → `/bellosoft-jira get [key]`
   - `tracker: plane` → `/bellosoft-plane get [sequence_id]`
4. **No tracker** — ask user: `"Enter ticket ID or press Enter to skip"`

Ticket ID formats:
- Jira: `PROJ-42`
- Plane: `NOKEY-42`
- None: omit from branch/commit (branch slug only, no ticket scope in commit)

---

## Command: BRANCH

### Step 1 — Resolve ticket ID (see above)

### Step 2 — Determine branch type

Infer from story title or issue type, or ask:

| Work type | Branch prefix |
|---|---|
| New feature | `feature` |
| Bug fix | `fix` |
| Refactor / cleanup | `chore` |
| Documentation | `docs` |
| Security / infra | `feature` |

### Step 3 — Build branch name

```
{type}/{ticket_id}-{slug}
e.g. feature/PROJ-42-user-auth-jwt
     fix/NOKEY-7-login-redirect-loop
     chore/refactor-payment-service    ← no tracker
```

Slug rules: lowercase story title → replace spaces/special chars with `-` → collapse `--` → truncate to 40 chars → strip trailing `-`.

### Step 4 — Check working tree

```bash
git status
```

If dirty → warn and offer: stash (`git stash`) or abort.
If not on `main` or `develop` → warn and ask whether to switch first.

### Step 5 — Create branch

```bash
git checkout -b {branch_name}
```

If branch exists → suggest `{branch_name}-2`, retry once, then halt.

### Step 6 — Output

```
✅ Branch created: {branch_name}
   Ticket: {ticket_id}

Next: implement, then /bellosoft-github commit
```

---

## Command: COMMIT

### Step 1 — Resolve ticket ID from branch name

```bash
git branch --show-current
```

Parse `{ticket_id}` from `{type}/{ticket_id}-*`. If no match → resolve via tracker (see top).

### Step 2 — Check for changes

```bash
git status --short
```

If clean → output `Nothing to commit.` and halt. Otherwise show changed files.

### Step 3 — Determine commit type

Infer from changed files or ask:

| Type | When |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Config, tooling, dependencies |
| `docs` | Documentation only |
| `refactor` | Structural change, no new feature |
| `test` | Tests only |

### Step 4 — Compose message

With ticket: `{type}({ticket_id}): {description}`
Without ticket: `{type}: {description}`

Validate: total length ≤ 72 characters.

### Step 5 — Stage and commit

```bash
git add -A
git commit -m "{message}"
```

If pre-commit hook fails → show error, halt. Never use `--no-verify`.

### Step 6 — Offer push

```
Push to remote? [y/n]
```

If yes:
```bash
git push --set-upstream origin {branch_name}
```

### Step 7 — Output

```
✅ Committed: {message}
   {pushed / "Not pushed yet — run 'git push' when ready"}
```

---

## Command: PR

### Step 1 — GitHub auth (resolved before anything else)

**Always read token file first. Run this exact command:**

```bash
# On Windows (PowerShell):
if (Test-Path ".secrets/github-token.txt") { Get-Content ".secrets/github-token.txt" -Raw }
# On Mac/Linux (bash):
cat .secrets/github-token.txt 2>/dev/null
```

**Resolution order (stop at first success):**

1. **Read `.secrets/github-token.txt`** — run the command above; if non-empty, authenticate:
   ```bash
   $env:GH_TOKEN = (Get-Content ".secrets/github-token.txt" -Raw).Trim()  # PowerShell
   export GH_TOKEN=$(cat .secrets/github-token.txt)                        # bash
   ```
   Then verify: `gh auth status`
2. Check `GH_TOKEN` or `GITHUB_TOKEN` env vars — if set, `gh` will use them automatically
3. Run `gh auth status` — if already authenticated, proceed silently
4. Only if all above fail, prompt:
   ```
   ⚠️ GitHub CLI not authenticated.
   Options:
     1. Run: gh auth login
     2. Save a personal access token to .secrets/github-token.txt
        (create at github.com → Settings → Developer settings → Personal access tokens)
   ```
   Once authenticated, save token to `.secrets/github-token.txt` for future sessions.

Ensure `.secrets/` is gitignored:
```bash
grep -qxF '.secrets/' .gitignore || echo '.secrets/' >> .gitignore
```

### Step 2 — Resolve ticket ID and story context

Extract from branch name. Fetch story title from tracker if needed (delegate to `/bellosoft-jira get` or `/bellosoft-plane get`).

### Step 3 — Ensure branch is pushed

```bash
git push --set-upstream origin {branch_name}
```

### Step 4 — Build PR title

**With tracker:**
```
[{ticket_id}] {story_title}
e.g. [PROJ-42] User authentication with JWT
     [NOKEY-7] Fix login redirect loop
```

The `[{ticket_id}]` bracket format activates automatic tracker state transitions:
- **Plane:** work item moves to Done when PR is merged (requires GitHub integration enabled in Plane)
- **Jira:** smart commit trigger (requires Jira GitHub integration)

**Without tracker:**
```
feat: {description}
```

### Step 5 — Build PR body

```markdown
## Summary

{one-line description of what this PR does}

## Tracker

[{ticket_id}]({tracker_url}) — {story_title}

## Acceptance Criteria

- [ ] {AC 1}
- [ ] {AC 2}

## Testing

- [ ] Build passes
- [ ] Existing tests pass
- [ ] Acceptance criteria verified
```

Show draft and ask: `Open PR with this description? [y/n/edit]`

### Step 6 — Create PR

```bash
gh pr create \
  --title "{pr_title}" \
  --body "{pr_body}" \
  --base {base_branch}
```

Detect base branch:
```bash
git remote show origin | grep "HEAD branch"
```

### Step 7 — Output

```
✅ PR created: {pr_url}
   Title: {pr_title}
   Tracker automation: ACTIVE (merging will update ticket state)

Next: /bellosoft-sync to update tracker to "In Review"
```

---

## Safety rules

- Never force-push without explicit user confirmation
- Never bypass pre-commit hooks (`--no-verify`)
- Never commit secrets — warn and halt if `.env` or `appsettings.*.json` appears in `git status`
- Always use brackets `[ticket_id]` in PR titles when a tracker is configured
