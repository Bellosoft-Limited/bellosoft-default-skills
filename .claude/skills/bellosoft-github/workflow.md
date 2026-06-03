# bellosoft-github — Workflow Reference

Supplementary reference loaded by the SKILL.md when needed.

---

## Branch naming examples

| Scenario | Branch |
|---|---|
| Jira story, feature | `feature/PROJ-42-user-auth-jwt` |
| Plane bug | `fix/NOKEY-7-login-redirect-loop` |
| No tracker, refactor | `chore/refactor-payment-service` |
| Hotfix | `fix/PROJ-99-null-ref-on-checkout` |

---

## Commit message examples

| Type | Message |
|---|---|
| Jira feature | `feat(PROJ-42): add JWT authentication middleware` |
| Plane fix | `fix(NOKEY-7): resolve redirect loop on login` |
| No tracker | `chore: upgrade dotnet to 9.0.5` |
| Test | `test(PROJ-42): add unit tests for auth service` |

---

## PR title examples

| Tracker | Title |
|---|---|
| Jira | `[PROJ-42] User authentication with JWT` |
| Plane | `[NOKEY-7] Fix login redirect loop` |
| None | `feat: add payment processing module` |

---

## Tracker state automation

### Plane
Requires GitHub integration enabled in Plane project settings.
PR title must contain `[IDENTIFIER-N]` with brackets.
On PR merge → Plane moves work item to the state mapped to "merged" in project settings.

### Jira
Requires Jira GitHub app or smart commits enabled.
Bracket format `[PROJ-42]` in PR title links the PR to the issue.
Transition via smart commit: include `#done` or `#in-review` in commit message if configured.

---

## Base branch detection

```bash
git remote show origin | grep "HEAD branch"
```

Default to `main`. Fall back to `develop` if `main` does not exist.
Never assume `master` — check first.

---

## Delegating tracker lookups

This skill never calls Plane or Jira MCP tools directly.

- Plane: delegate to `/bellosoft-plane get {sequence_id}`
- Jira: delegate to `/bellosoft-jira get {issue_key}`

Both return a structured story object with `title`, `status`, `acceptance_criteria`.
