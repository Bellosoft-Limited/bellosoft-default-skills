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

### Acceptance criteria → tests
| AC | Test | Behaviour |
|----|------|-----------|
| 1 | `ShouldDoX_WhenY` | [≤10 words] |
| 2 | `ShouldFailWith_WhenZ` | [≤10 words] |

### Files
+ `path/new.ext` — [≤8 words]
~ `path/existing.ext` — [≤8 words]

### Steps
1. [Imperative, ≤12 words] → tests 1, 2
2. ...

### Out of scope
- [item]

### Questions
- [Blocking only. Yes/no answer.]
```

Rules:
- Every AC has at least one test. If not, write `AC n — no test: [reason]`.
- Include test files in `Files`. `bellosoft-dev-execute` reads them from there.
- One step = one file when possible. Each step names the tests it makes pass.
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
✅ approve · ✏️ [feedback] · 🔍 explain N · ❌ cancel
```

- `approve` → save the plan. See below. Do **not** run `/bellosoft-dev-execute`.
- `explain N` → expand step or test N in 3–5 lines. Nothing else.
- `cancel` → stop. The dev can code without a plan.

**Do NOT write code until the developer approves. After approval, still write no code.**

### On approve

1. Save the plan to `docs/dev-plans/[ID]-[kebab-title].md`. Create the folder if missing.
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
   Plan saved: docs/dev-plans/[file].md (commit it with the story work)
   Next: start a new context window, then run
     /bellosoft-dev-execute docs/dev-plans/[file].md
   ```

Stop there. Do not start execution in this session.
