---
name: bellosoft-dev-execute
description: >
  Executes a plan approved and saved by /bellosoft-dev-plan (docs/planning-artifacts/dev-plans/*.md).
  Use this skill when the user types /bellosoft-dev-execute [plan path], ideally in a
  new context window. Follows strict TDD: writes ALL test cases first, confirms they
  fail, then implements the code to make them pass, one step at a time. Never skip
  the red-phase. Do NOT invoke on general coding tasks or without an approved plan.
---

# Skill: bellosoft-dev-execute

## Purpose
Execute an approved story implementation plan with strict Test-Driven Development.
The golden rule: **tests exist and fail before any production code is written.**

## Prerequisite
A plan must be saved by `/bellosoft-dev-plan` in `docs/planning-artifacts/dev-plans/` with `status: approved`.

Find the plan:
1. Argument is a path → read that file.
2. Argument is a ticket ID → read `docs/planning-artifacts/dev-plans/[ID]-*.md`.
3. No argument → list `docs/planning-artifacts/dev-plans/*.md` with `status: approved`. If one file, confirm it: `Execute docs/planning-artifacts/dev-plans/X.md? (yes/no)`. If several, ask which.

If the file is missing or not `status: approved`, stop and show:

```
No approved plan found.

Options:
  1. /bellosoft-dev-plan PROJ-123          ← fetch ticket and generate a plan first
  2. /bellosoft-dev-plan "description"     ← describe what you want to build
  3. Skip planning — just code it yourself (no skill needed)
```

Do NOT infer a plan from chat history or start coding without one.

---

## Execution Protocol

Read the whole plan before Phase 1. `Decisions` override the ticket text. Do not "fix" code
to match the ticket where a decision says otherwise. `Accepted risks` are not bugs to fix.

### Phase 1 — RED: Write All Tests

1. Create or edit the test file(s) listed in the plan's `Files`
2. Write every test from the plan's `Tests` table, in `#` order. Apply the plan's `Test setup`.
3. Make the tests compile with **scaffolding only** — no production behaviour yet:
   - Run plan step 0 if it exists.
   - If there is no step 0 and the tests do not compile, add the minimum: new properties,
     method signatures, constructor parameters, stubs that throw `NotImplementedException`
     (or the language equivalent). Only in files listed in `Files`.
   - Build the solution (or the project, if there is no solution). Fix any caller the scaffold broke,
     with scaffolding only. A caller outside `Files` → pause and ask.
   - List every scaffold change for the developer.
4. Run the tests:
   ```bash
   # .NET
   dotnet test --filter "ClassName"
   # Node / TS
   npx vitest run path/to/spec
   ```
5. Check the result:
   - Every non-guard test fails, for the expected reason (assertion or `NotImplementedException`, not a setup crash).
   - Every `(guard)` test passes.
   - Existing tests in the same test classes still pass.
6. If a non-guard test passes, it does not test the new behaviour. Strengthen it (see `Test setup`)
   and re-run. If it still passes, pause and ask: mark it `(guard)`, or rewrite it?
   If a guard test fails, pause and explain. Do not change production code to fix it.
7. Show the failing output to the developer
8. Only proceed to Phase 2 after the red state is confirmed

If the project has no test runner available, note it explicitly and ask how to proceed.

---

### Phase 2 — GREEN: Implement Step by Step

Work through the implementation steps from the plan **one at a time**:

For each step:
1. State what you are about to do: `▶ Step N: [description]`
2. Make the minimal change needed to pass the relevant test(s)
3. Run the test(s) for that step, plus the guard tests and the existing tests in the same test classes:
   - ✅ Passing → move to next step
   - ❌ Still failing → diagnose, fix, re-run (max 2 attempts before pausing to explain)
4. Never implement ahead — only what the current step requires
5. If a step's test can only pass after a later step, the plan's order is wrong.
   Do not pull the later step forward silently. Pause, explain, and propose the new order.
6. Steps with no test (migration, docs, build): verify the way the step says, e.g. build or command output.
   Manual steps (e.g. a check in a local database): do not mark them done. List them in the summary.

---

### Phase 3 — REFACTOR: Clean Up

After all tests pass:
1. Review the new code for obvious duplication, naming clarity, missing edge-case guards
2. **Check cyclomatic complexity** — for every method/function written in this story:
   - Count decision points (each `if`, `else if`, `for`, `foreach`, `while`, `case`, `catch`, `&&`, `||`, `??`, ternary `?:` adds 1; start from 1)
   - **Threshold: > 10 is a warning, > 15 must be refactored before proceeding**
   - If over threshold: extract private methods, introduce early returns, replace conditionals with polymorphism or strategy pattern — whatever fits the existing codebase conventions
   - Re-run tests after each refactor to confirm green
3. Make other refactor changes — **tests must remain green throughout**
4. Run the full test suite one final time

---

### Phase 4 — Scope Change Protocol

If during execution you discover the story scope is larger than planned, or a
dependency is missing, **stop immediately** and surface it:

```
⚠️ Scope issue discovered at Step N

What I found: [specific file/behaviour/missing dependency]

Options:
  1. Expand scope — continue with the extra work included (adds ~Xh)
  2. Scope down — skip [specific part], note as follow-up story
  3. Block — this story cannot be completed without [prerequisite]; suggest creating a blocker ticket

Which would you prefer?
```

Do NOT silently expand scope or work around the issue. The developer decides.

If option 3 (blocker) is chosen, output a ready-to-use ticket description:
```
## Blocker ticket — [short title]
**Blocks:** [current story ID]
**What's needed:** [description]
**Suggested size:** [XS/S/M]
```
The developer can paste this into Jira directly.

---

### Phase 5 — Summary

Output a completion summary:

```
## ✅ Execution Complete — [STORY-ID]

### Tests
- Written: N (guards: N)
- Passing: N
- Skipped: 0

### Files Changed
- Created: [list]
- Modified: [list]

### Manual steps left
- Step N: [what the developer must check by hand]

### Notes
[Any deviations from the plan, and why — including steps reordered and tests re-marked as guards]

---
Next step: /bellosoft-dev-review   ← validate against acceptance criteria
```

---

## Hard Rules

- Never skip the RED phase. If you cannot run tests, say so explicitly.
- Never implement more than one step ahead of the current passing test.
- If a step requires touching a file not in the plan, pause and ask before proceeding.
- Never commit. The developer controls git.
- Never silently expand scope — always surface and ask.
