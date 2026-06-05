---
name: bellosoft-dev-review
description: >
  Invoked after /bellosoft-dev-execute completes, or when the developer wants to validate
  their implementation against a story. Use when the user types /bellosoft-dev-review,
  says "review this", "check the story", "is this done?", or "validate AC".
  Reads the original story (local .md, Jira ticket, or Plane ticket), maps each
  acceptance criterion to the actual code and tests, and produces a pass/fail
  verdict per criterion. Highlights gaps, missing edge cases, and anything that
  would block the story from being marked Done. Does NOT rewrite code — only audits
  and reports. THIS SKILL IS OPTIONAL — devs can self-review directly in Jira/Plane.
---

# Skill: bellosoft-dev-review

## Purpose
Validate the implementation against the original story's acceptance criteria.
Produce a clear pass/fail report so the developer knows if the story is
genuinely done or still has gaps.

This skill is **optional**. Developers can review their own work and mark
stories Done in Jira/Plane without using it.

---

## Step 1 — Reload the Story

Use the same input resolution as `/bellosoft-dev-plan`:
- Jira ticket ID → delegate to `/bellosoft-jira get [issue_key]`
- Plane ticket ID → delegate to `/bellosoft-plane get [sequence_id]`
- Local `.md` file → read directly
- No argument → look for most recently modified story file

Extract every acceptance criterion as a checklist item.

---

## Step 2 — Audit the Implementation

For each acceptance criterion:

1. **Find the test(s)** that cover it — read the test file
2. **Find the production code** that satisfies it — read the implementation
3. **Run the tests** to confirm current state:
   ```bash
   dotnet test   # or vitest run / jest / etc.
   ```
4. Assess:
   - Is there a test for this AC? (yes / no / partial)
   - Does the test actually assert the right behaviour?
   - Is the test passing?
   - Is the production code correct and complete?

---

## Step 3 — Produce the Review Report

```
## Code Review — [STORY-ID]: [Title]

### Acceptance Criteria Checklist

| AC | Description | Test Exists | Test Passes | Code Complete | Status |
|----|-------------|-------------|-------------|---------------|--------|
| 1  | ...         | ✅ / ❌ / ⚠️ | ✅ / ❌      | ✅ / ❌ / ⚠️  | ✅ Done / ❌ Blocked / ⚠️ Partial |

### Issues Found
[For each ❌ or ⚠️ above, explain what is missing or wrong]

### Out-of-Scope Check
[Confirm no unintended changes were made outside the story scope]

### Cyclomatic Complexity
For every method/function added or modified by this story:
- Count: start at 1, add 1 for each `if`, `else if`, `for`, `foreach`, `while`, `case`, `catch`, `&&`, `||`, `??`, ternary `?:`
- Report any method exceeding threshold:

| Method | Complexity | Threshold | Status |
|--------|-----------|-----------|--------|
| `MethodName` | N | 10 | ✅ OK / ⚠️ Warning (>10) / ❌ Must refactor (>15) |

If any method scores > 15: mark verdict as ⚠️ NEEDS WORK regardless of AC status.

### Code Quality Notes
[Optional: naming, structure, anything worth a comment — keep brief]

### Verdict
✅ READY — all ACs covered, all tests passing. Story can be marked Done.
⚠️  NEEDS WORK — [N] issues above must be resolved first.
❌ BLOCKED — [reason — e.g. tests not running, major AC not implemented]
```

---

## Step 4 — Next Steps

### If verdict is ✅ READY

```
Story is complete. Suggested next steps:

  Commit:
    git add -A
    git commit -m "feat([STORY-ID]): [short description]"

  Sync tracker & open PR (run these skills):
    /bellosoft-sync       ← marks story Done in Jira/Plane, adds review comment
    /bellosoft-github     ← creates PR with correct title format for auto-linking

  Or do it manually:
    - Mark [STORY-ID] as Done in Jira/Plane
    - Open PR titled: [[STORY-ID]] [short description]
```

### If verdict is ⚠️ or ❌

```
Issues listed above. Options:
  - Fix manually and re-run /bellosoft-dev-review
  - Ask Claude to fix a specific issue: "fix AC-3"
```

---

## Hard Rules

- Never silently pass an AC that has no test. Mark it ⚠️ at minimum.
- Do not rewrite code during review — only report.
- If tests cannot be run, say so clearly and mark all test-dependent ACs as ⚠️ unverified.
- Any method with cyclomatic complexity > 15 **blocks** a ✅ READY verdict — must be reported as ❌ in the complexity table and flagged in Issues Found.
