---
name: bellosoft-dev-plan
description: >
  Invoked when the developer wants AI help planning a story before coding. Use this skill
  when the user types /bellosoft-dev-plan, mentions a Jira ticket ID (PROJ-123),
  a story file path (.md), or says "start story", "plan this story", "help me implement STORY-123".
  Accepts a local .md file, a Jira ticket ID or URL, or pasted story content.
  Produces a short implementation plan with TDD approach — tests listed BEFORE
  implementation steps. Waits for explicit approval before any code is written.
  THIS SKILL IS OPTIONAL — devs can work directly from Jira without it.
  Do NOT auto-invoke on general coding tasks.
---

# Skill: bellosoft-dev-plan

Optional. Not a gate. Devs can work from Jira without it.
Use it when the story is complex enough that a plan saves time.

```
/bellosoft-dev-plan PROJ-123                        ← Jira ticket ID
/bellosoft-dev-plan https://belloprojects.atlassian.net/...   ← Jira URL
/bellosoft-dev-plan path/to/story.md                ← local file
/bellosoft-dev-plan "add password reset to login"   ← free-form text
/bellosoft-dev-plan                                 ← pasted content, or latest story .md
```

---

## Step 0 — Tracker

If `docs/planning-artifacts/status.md` has `tracker:` → skip.
Otherwise load `.claude/skills/bellosoft-jira/references/tracker-bootstrap.md`.

## Step 1 — Load the story

Load `references/load-story.md`. It covers each input type.
Extract: title/ID, goal, numbered ACs, technical notes, out of scope.

If ACs are missing, ask: `No ACs. Define ACs first, or continue without? (define / continue)`

## Step 2 — Load parent context

Load `references/parent-context.md`. Fetch parents silently.
Do not print a context block. Use one line in the plan (`E2 › S3 › T5`).
If a parent cannot be fetched, continue with what is available.

## Step 3 — Analyse the codebase

If `docs/planning-artifacts/codebase-audit.md` exists:
- Read Module Inventory, Established Conventions, Tech Debt Register.
- Follow the conventions in all new code.
- Re-read only the affected files if the audit is older than 14 days or misses a module.

If no audit exists, read only the relevant code:
- Find the files this story touches (`Glob`, `Grep`, `Read`).
- Find the test framework and test file naming.
- Find similar code to copy patterns from.

## Step 4 — Write the plan

Use this format. Omit any section with no content. Never write "None".

```
## Plan — [ID]: [Title]
[Epic ID] › [Story ID] › [Task ID]

### Tests
| # | Covers | Test | Behaviour |
|---|--------|------|-----------|
| 1 | AC1 | `ShouldDoX_WhenY` | [≤12 words] |
| 2 | AC2, D1 | `ShouldFailWith_WhenZ` | [≤12 words] |
| 3 | AC2 | `ShouldKeepX_WhenW` (guard) | [≤12 words] |

### Test setup
- [Fixture or data choice that makes the tests meaningful. ≤20 words.]

### Files
- new `path/new.ext` — [≤8 words]
- edit `path/existing.ext` — [≤8 words]

### Steps
0. Scaffold: [members the tests need to compile]. No behaviour. Verify: solution builds.
1. [Imperative, ≤12 words] → tests 1, 2
2. ...

### Decisions
- D1: [What was decided] — [reason]

### Accepted risks
- [Risk] — [why accepted]

### Out of scope
- [item]

### Questions
- [Blocking only. Yes/no answer.]
```

Rules for `Tests`:
- Number every test. Steps refer to tests by `#`.
- `Covers` names the source: `ACn`, `Dn`, or the ticket's own label (e.g. `S2`). Never a bare "Rule".
- Every AC has at least one test. If not, write `ACn — no test: [reason]`.
- Mark a test `(guard)` when it passes before any change. A guard protects existing behaviour.
  Prefer an assertion that fails first, e.g. a log check, over a guard.
- `Test setup` holds what the Behaviour cell cannot: fixtures, and data that makes a wrong path fail.
  Example: "Saved figures differ from a recalculation, so recalculating fails the test."

Rules for `Steps`:
- Step 0 lists only what the tests need to compile: properties, signatures, constructor parameters.
  Omit step 0 if the tests compile against today's code.
- Step 0 ends with "Verify: solution builds" (or the project, if there is no solution).
  A changed signature can break callers outside the test classes.
- Each non-guard test appears in exactly one step: the step that turns it green.
- Split a step that turns more than about 4 tests green. Slice by behaviour, e.g. matching, grouping, labels.
- Order the steps so each step's tests pass after that step and the steps before it.
  Check every hop, e.g. a value copied in a later step that the earlier step reads.
- One step = one file when possible. Steps with no test (migration, docs, manual check) say how to verify them.

Rules for the other sections:
- Include test files in `Files`. `bellosoft-dev-execute` reads them from there.
- Write each `Files` entry as its own `- ` list item, one per line. Never start a line with `+` or `~`.
- `Decisions` is required when the plan departs from the ticket or spec text. One line each, with the reason.
  `bellosoft-dev-review` reads it, so an approved departure is not reported as a failed AC.
- A decision is a choice between real alternatives, or a departure from the ticket.
  Implementation notes go in `Steps`. Cite each decision in the `Covers` column of the test that checks it.
- `Accepted risks` holds known trade-offs the dev accepted. `Questions` holds only blocking items.
- No summary paragraph. The table and steps are the summary.
- Add story ACs the task does not cover only if they affect this task.

### Writing style (simplified technical English)
- Maximum 20 words per sentence. One instruction per sentence.
- Use imperative and active voice: "Add `ResetToken`", not "`ResetToken` should be added".
- Use one word for one thing. Always "test" (not spec, scenario, case). Always "file" (not module, artifact).
- Do not use idioms or filler: "in order to", "make sure that", "leverage", "robust".
- Table cells are fragments, not sentences.
- Put the reason after a dash. Skip the reason if the step name is clear.

| Avoid | Write |
|-------|-------|
| "We should make sure that the token is validated before it is used" | "Validate token before use" |
| "This will update the controller so that it handles the new error case" | "Handle `TokenExpired` in controller" |
| "There is a risk that the email service might not be available" | "Is the email service mocked in tests? (yes/no)" |

## Step 5 — Wait for approval

End the plan with:

```
---
✅ approve · ✏️ [feedback] · 🔍 explain step N | test N · ❌ cancel
```

- `approve` → save the plan. See below. Do **not** run `/bellosoft-dev-execute`.
- `explain step N` or `explain test N` → expand that step or test in 3–5 lines. Nothing else.
- `cancel` → stop. The dev can code without a plan.

**Do NOT write code until the developer approves. After approval, still write no code.**

### On approve

1. Save the plan to `docs/planning-artifacts/dev-plans/[ID]-[kebab-title].md`. Create the folder if missing.
   Overwrite the file if it exists for the same ID.
2. File content: the approved plan, exactly as approved (include any feedback changes),
   with this header:

   ```
   ---
   ticket: [ID]
   status: approved
   approved: [YYYY-MM-DD]
   ---
   ```
3. Do not stage or commit the file. The developer controls git.
   The plan is a project record. The developer commits it with the story work.
4. Reply with only this:

   ```
   Plan saved: docs/planning-artifacts/dev-plans/[file].md (commit it with the story work)
   Next: start a new context window, then run
     /bellosoft-dev-execute docs/planning-artifacts/dev-plans/[file].md
   ```

Stop there. Do not start execution in this session.
