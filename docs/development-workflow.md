# Development Workflow

## Phase 1 — Pick & Prep the Story

**Step 1 — Find your assigned ticket**

In Copilot/Claude chat:
```
/bellosoft-sprint
```
Shows your active sprint items grouped by status (Blocked 🔴, In Progress 🟡, To Do ⚪, Done ✅) with quick-start commands for each story. Alternatively, open your tracker (Jira/Plane) directly and note the ticket ID (e.g. `PROJ-42` or `NOKEY-42`).

**Step 2 — Plan the story**

In Copilot/Claude chat (Agent mode):
```
/bellosoft-dev-plan PROJ-42
```
Fetches the story from your tracker, loads relevant codebase context, and produces a TDD implementation plan — test cases listed before implementation steps. Review and approve the plan before proceeding.

> Skipping this step is fine. You can code directly from the ticket or paste the story as free text. The skill is a tool, not a gate.

**Step 3 — Create branch and move ticket to In Development**

In Copilot/Claude chat:
```
/bellosoft-github branch
/bellosoft-plane update NOKEY-42 transition "In Development"
```
or for Jira:
```
/bellosoft-github branch
/bellosoft-jira update PROJ-42 transition "In Progress"
```

Creates a tracker-compatible git branch (e.g. `feature/PROJ-42-story-slug`) and moves the ticket to **In Development / In Progress**.

---

## Phase 2 — Implement

**Step 4 — Execute the story**

If you ran `/bellosoft-dev-plan` in Step 2, execute the approved plan:
```
/bellosoft-dev-execute
```
The agent follows the TDD cycle: write failing tests (RED) → implement (GREEN) → clean up (REFACTOR). If unexpected scope is discovered mid-implementation it surfaces the issue and pauses — never silently expands scope.

> You can also implement manually without any skill. The PR checklist and review step apply either way.

**Step 5 — Backend build gate** *(mandatory before continuing)*
```bash
cd src && dotnet build
```
Must be zero errors. Fix before proceeding.

**Step 6 — Frontend build gate** *(if frontend was touched)*
```bash
cd src/<project>.Web && npm run build
```
Must be zero errors.

---

## Phase 3 — Review & Ship

**Step 7 — Code review**

In Copilot/Claude chat (Agent mode):
```
/bellosoft-dev-review
```
Validates the implementation against the story's acceptance criteria. Produces a pass/fail report. If ✅ READY — all ACs covered, no blockers — proceed to Step 8.

**Step 8 — Run automated tests**

Backend stories:
```bash
dotnet test
```

Frontend stories:
```bash
npm run test:e2e
```

Full-stack: both. Fix any failures before continuing.

> **Backend-only stories** (infrastructure, APIs, jobs): xUnit tests in `src/<project>.Tests/`.
>
> **Frontend stories** (UI, forms, workflows): Playwright specs in `src/<project>.Web/e2e/`.

**Step 9 — Commit and create PR**

In Copilot/Claude chat:
```
/bellosoft-github commit
/bellosoft-github pr
```
Commits with a conventional message linked to the ticket (`feat(PROJ-42): description`). PR title uses `[PROJ-42]` bracket format to activate tracker state automation on merge.

**Step 10 — Sync tracker to In Review**

In Copilot/Claude chat:
```
/bellosoft-plane update NOKEY-42 transition "In Review"
```
or for Jira:
```
/bellosoft-jira update PROJ-42 transition "In Review"
```
Adds a review comment with AC coverage summary and moves the ticket to **In Review**.

**Step 11 — Manually verify on QA**

Deploy the branch to the QA environment and smoke-check against the acceptance criteria before handing off. Push a new commit if anything needs fixing.

**PR checklist (reviewer):**
- [ ] Branch name follows company standards (`feature/` or `fix/`)
- [ ] Target branch is correctly set
- [ ] No conflicts
- [ ] No build errors
- [ ] Description is clear and links to the ticket
- [ ] Test evidence matches task complexity
- [ ] Code follows quality and security standards
- [ ] Code is optimised and clean given time/complexity constraints
- [ ] Implements the requested changes
- [ ] Edge cases are handled
- [ ] Cross-cutting concerns considered
- [ ] Automated tests are reliable and cover meaningful scenarios
- [ ] Reviewer understands what the code does and why
- [ ] Large refactors out of scope are raised as new tasks, not change requests

Also covered in the [Code Reviewer checklist](https://bellosoft.getoutline.com/doc/development-checklists-8AdcC8oMVh#h-code-reviewer-checklist).

**PR SLA:**
- Review within 2 business hours
- 2 approvals required, at least one meaningful: FE PRs need 1 senior FE, BE PRs need 1 senior BE
- No AI-generated code ships without human review
- The developer who opens the PR owns every line in it, regardless of who or what wrote it
- The developer who opens the PR is responsible for completing it once approved
- If reviewers cannot meet this SLA, flag immediately — do not silently ignore the PR

**Exit condition:** All checklist items addressed.

**Step 12 — Move ticket to Ready for QA**

Move the ticket from **In Review** to **Ready for QA**. This signals to QA that dev has pre-validated the deployment.

- Testers start review as soon as possible, testing the specific changes
- If all correct, testers run the full test suite to validate no regression
- Once QA is declared sane, tasks are closed and the team is notified the deploy can proceed
  - Depending on the project there may be a UAT phase before Production

> *Deployments are blocked when code that reaches develop fails the test phase. Any code merged after the broken code is blocked from production until the fix is merged and tested.*
>
> *The goal is per-PR environments so merged code is always deploy-ready. Until then, QA must follow merge order.*

**Exit condition:** Changes on QA, tested, and ready for UAT/Production.

---

## Development Summary Table

| Step | Who | Where | Command / Action | Result |
|------|-----|-------|------------------|--------|
| 1 | Dev | Chat | `/bellosoft-sprint` | Sprint overview, pick your story |
| 2 | Dev | Chat | `/bellosoft-dev-plan PROJ-42` | TDD implementation plan produced and approved |
| 3 | Dev | Chat | `/bellosoft-github branch` + update tracker | Branch created, ticket → **In Development** |
| 4 | Dev | Chat | `/bellosoft-dev-execute` | Code implemented with TDD |
| 5 | Dev | Terminal | `dotnet build` | Zero errors confirmed |
| 6 | Dev | Terminal | `npm run build` | Zero errors confirmed (frontend only) |
| 7 | Dev | Chat | `/bellosoft-dev-review` | ACs validated, ✅ READY confirmed |
| 8 | Dev | Terminal | `dotnet test` / `npm run test:e2e` | All tests pass |
| 9 | Dev | Chat | `/bellosoft-github commit` + `/bellosoft-github pr` | PR opened with `[PROJ-42]` title |
| 10 | Dev | Chat | Update tracker transition "In Review" | Ticket → **In Review** |
| 11 | Dev | Manual | Smoke-check on QA environment | ACs pre-validated by dev |
| 12 | Dev | Tracker | Move ticket to **Ready for QA** | Ticket → **Ready for QA** |
