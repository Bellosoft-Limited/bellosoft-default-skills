# Git Flow
> Branching model: GitFlow classic
> Stack: Git · GitHub · conventional commits

---

## Branch Structure

| Branch | Purpose | Lifetime |
|---|---|---|
| `main` | Production-ready code only. Every commit on `main` is a release. | Permanent |
| `develop` | Integration branch. All completed features merge here. | Permanent |
| `feature/*` | One feature or story per branch. | Until merged to `develop` |
| `release/*` | Stabilization before a production release. | Until merged to `main` + `develop` |
| `hotfix/*` | Urgent production fixes. | Until merged to `main` + `develop` |

---

## Branch Naming

```
feature/<ticket-id>-short-description
release/<version>
hotfix/<ticket-id>-short-description
```

Examples:
- `feature/PROJ-42-user-authentication`
- `release/1.4.0`
- `hotfix/PROJ-99-fix-payment-timeout`

Rules:
- Lowercase, hyphens only. No spaces, no underscores, no forward slashes within the name segment.
- Always include the ticket/story ID.
- Description is kebab-case, max ~5 words.

---

## Commit Messages

Format: **Conventional Commits** (`type(scope): description`)

```
<type>(<scope>): <short description>

[optional body]

[optional footer — e.g. Closes #42, BREAKING CHANGE: ...]
```

### Types

| Type | When to use |
|---|---|
| `feat` | New feature or user-facing capability |
| `fix` | Bug fix |
| `refactor` | Code change that is neither a feature nor a fix |
| `chore` | Tooling, config, dependency updates |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `ci` | CI/CD pipeline changes |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace (no logic change) |
| `revert` | Reverting a previous commit |

### Rules
- Description is lowercase, present tense, imperative mood: `add user login` not `Added user login`.
- Max 72 characters in the subject line.
- No period at the end of the subject line.
- Breaking changes: append `!` after type/scope (`feat!:`) and add `BREAKING CHANGE:` in the footer.
- Reference tickets in the footer: `Closes #42`, `Refs PROJ-42`.

---

## Workflow

### Starting a feature
```bash
git checkout develop
git pull origin develop
git checkout -b feature/PROJ-42-user-authentication
```

### Finishing a feature
```bash
# Rebase on develop before PR (keeps history clean)
git fetch origin
git rebase origin/develop

# Open PR: feature/* → develop
# Require at least 1 review approval before merge
# Use Squash merge for single-commit features, Merge commit for multi-commit stories
```

### Creating a release
```bash
git checkout develop
git pull origin develop
git checkout -b release/1.4.0
# Only bug fixes and version bump commits go on release/* branches
# No new features on release branches
```

### Finishing a release
```bash
# Merge release/* → main (via PR)
# Tag main with the version: git tag -a v1.4.0 -m "Release 1.4.0"
# Merge release/* → develop (to capture release fixes)
# Delete the release branch
```

### Hotfix
```bash
git checkout main
git pull origin main
git checkout -b hotfix/PROJ-99-fix-payment-timeout
# Fix the issue
# Merge hotfix/* → main (via PR, tag the release)
# Merge hotfix/* → develop
```

---

## Pull Request Rules

- PRs must target the correct branch (`feature/*` → `develop`, `hotfix/*` → `main`).
- PR title follows Conventional Commits format.
- Every PR must reference a ticket in the description.
- Minimum 1 reviewer required. 2 reviewers for changes to `main` or security-sensitive code.
- CI must pass (build + tests + lint) before merge.
- No force pushes to `main` or `develop`.
- Delete the source branch after merge.
- Do not merge your own PR without review unless explicitly permitted.

---

## Tagging

- Tags are applied to `main` only, after a successful release merge.
- Format: `v<semver>` — e.g. `v1.4.0`, `v1.4.1`.
- Use annotated tags: `git tag -a v1.4.0 -m "Release 1.4.0"`.
- Push tags explicitly: `git push origin --tags`.

---

## What to Never Do

- Never commit directly to `main` or `develop`. All changes go through PRs.
- Never force push to `main` or `develop`.
- Never use `git reset --hard` on shared branches.
- Never include generated files, build artifacts, or secrets in commits.
- Never create long-lived feature branches (> 1 sprint). Break large work into smaller stories.
- Never merge `main` back into `develop` manually — use the release branch flow.
