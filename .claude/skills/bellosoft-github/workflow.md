# bellosoft-github — Workflow Reference

Supplementary reference loaded by the SKILL.md when needed.

---

## Branch naming examples

Format: `{type}/{ticket_id}/{slug}` (slash-separated). No ticket → `{type}/{slug}`.

| Scenario | Branch |
|---|---|
| Jira story, feature | `feature/PROJ-42/user-auth-jwt` |
| Plane bug | `fix/NOKEY-7/login-redirect-loop` |
| No tracker, refactor | `chore/refactor-payment-service` |
| Hotfix | `fix/PROJ-99/null-ref-on-checkout` |

---

## Commit message examples

With ticket: `#{ticket_id}: {description}`. Without ticket: `{type}: {description}`. Total length ≤ 72 chars.

| Type | Message |
|---|---|
| Jira feature | `#PROJ-42: add JWT authentication middleware` |
| Plane fix | `#NOKEY-7: resolve redirect loop on login` |
| No tracker | `chore: upgrade dotnet to 9.0.5` |
| Test, no tracker | `test: add unit tests for auth service` |

---

## PR title examples

With tracker: `#{ticket_id}: {story_title}`. Without tracker: `{type}: {description}`.

| Tracker | Title |
|---|---|
| Jira | `#PROJ-42: User authentication with JWT` |
| Plane | `#NOKEY-7: Fix login redirect loop` |
| None | `feat: add payment processing module` |

The `#{ticket_id}` prefix (not brackets) is what activates automatic tracker state transitions.

---

## Tracker state automation

Both trackers are triggered by the `#{ticket_id}` format in the PR title.

### Plane
Requires GitHub integration enabled in Plane project settings.
On PR merge → Plane moves the work item to **Done**.

### Jira
Requires the Jira GitHub integration (smart commits) enabled.
The `#PROJ-42` reference in the PR title links the PR to the issue and drives the transition.

---

## Base branch detection

```bash
git remote show origin | grep "HEAD branch"
```

Default to `main`. Fall back to `develop` if `main` does not exist.
Never assume `master` — check first.

---

## Ticket ID resolution

Resolve `{ticket_id}` in this order (see SKILL.md for full detail):

1. **User provided** — e.g. `/bellosoft-github branch PROJ-42`
2. **Current branch name** — parse the `{type}/{ticket_id}/{slug}` pattern
3. **Tracker lookup** — read `docs/planning-artifacts/status.md` for `tracker:`, then delegate:
   - `tracker: jira` → `/bellosoft-jira get [key]`
   - `tracker: plane` → `/bellosoft-plane get [sequence_id]`
4. **No tracker** — omit the ticket from branch/commit (slug only, no ticket scope).

This skill never calls Plane or Jira MCP tools directly — it always delegates to
`/bellosoft-jira get` or `/bellosoft-plane get`, which return a structured story
object with `title`, `status`, and `acceptance_criteria`.
