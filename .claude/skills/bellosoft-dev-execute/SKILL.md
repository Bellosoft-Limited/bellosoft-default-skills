---
name: bellosoft-dev-execute
description: >
  Invoked after the developer approves a plan from /bellosoft-dev-plan. Use this skill
  when the user types /bellosoft-dev-execute, says "approve", "proceed", "start coding",
  or "go ahead" after a dev-story plan has been presented. Executes the
  approved implementation plan following strict TDD: writes ALL test cases
  first, confirms they fail, then implements the code to make them pass, one
  step at a time. Never skip the red-phase. Do NOT invoke on general coding
  tasks or before a plan has been approved.
---

# Skill: bellosoft-dev-execute

## Purpose
Execute an approved story implementation plan with strict Test-Driven Development.
The golden rule: **tests exist and fail before any production code is written.**

## Prerequisite
A plan must have been produced by `/bellosoft-dev-plan` and explicitly approved.
If no prior plan exists in context, stop and show:

```
No approved plan found in this session.

Options:
  1. /bellosoft-dev-plan PROJ-123          ← fetch ticket and generate a plan first
  2. /bellosoft-dev-plan "description"     ← describe what you want to build
  3. Skip planning — just code it yourself (no skill needed)

/bellosoft-dev-execute only runs against an approved plan.
If you want to code without a plan, work directly without this skill.
```

Do NOT attempt to infer a plan from context or start coding without one.

---

## Execution Protocol

### Phase 1 — RED: Write All Tests

1. Create the test file(s) listed in the approved plan
2. Write every test case from the plan's test table
3. Tests must be **compilable but failing** — do not write production code yet
4. Run the test suite to confirm all new tests fail:
   ```bash
   # .NET
   dotnet test --filter "ClassName"
   # Node / TS
   npx vitest run path/to/spec
   ```
5. Show the failing output to the developer
6. Only proceed to Phase 2 after confirming failures

If the project has no test runner available, note it explicitly and ask how to proceed.

---

### Phase 2 — GREEN: Implement Step by Step

Work through the implementation steps from the plan **one at a time**:

For each step:
1. State what you are about to do: `▶ Step N: [description]`
2. Make the minimal change needed to pass the relevant test(s)
3. Run the test(s) for that step:
   - ✅ Passing → move to next step
   - ❌ Still failing → diagnose, fix, re-run (max 2 attempts before pausing to explain)
4. Never implement ahead — only what the current step requires

---

### Phase 3 — REFACTOR: Clean Up

After all tests pass:
1. Review the new code for obvious duplication, naming clarity, missing edge-case guards
2. Make refactor changes — **tests must remain green throughout**
3. Run the full test suite one final time

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
The developer can paste this into Jira/Plane directly.

---

### Phase 5 — Summary

Output a completion summary:

```
## ✅ Execution Complete — [STORY-ID]

### Tests
- Written: N
- Passing: N
- Skipped: 0

### Files Changed
- Created: [list]
- Modified: [list]

### Notes
[Any deviations from the plan, and why]

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
