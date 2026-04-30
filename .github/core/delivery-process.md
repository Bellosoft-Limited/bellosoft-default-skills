# Delivery Process
> Bellosoft delivery workflow — sprint-based with BMAD story execution
> Stack-agnostic. Applies to all projects.

---

## Sprint Structure

| Phase | Activity |
|---|---|
| Sprint Planning | Review prioritized backlog, assign stories to sprint, confirm story is ready (acceptance criteria, designs, dependencies clear) |
| Development | Implement one story at a time per developer. Branch per story. |
| Code Review | PR opened, reviewed, CI passes, approved. |
| QA | Acceptance criteria verified against the story definition. E2E or manual test on staging. |
| Sprint Review | Demo completed work. Product stakeholder acceptance. |
| Retrospective | Post-sprint lessons captured. |

Sprint length: **2 weeks** (default). Adjust per project.

---

## Story Lifecycle

```
Backlog → Ready → In Progress → Review → QA → Done
```

### Backlog
- Story is created from the epic.
- Acceptance criteria are written (Given/When/Then or bullet conditions).
- Story is estimated and prioritized.

### Ready
- Story has clear acceptance criteria.
- Designs or wireframes attached (if UI work).
- Dependencies identified and unblocked.
- Story fits within one sprint.

### In Progress
- Developer creates branch: `feature/<id>-short-name`.
- Development follows the story file as the implementation spec.
- Only one story per developer in progress at a time (WIP limit = 1).

### Review
- PR opened against `develop`.
- PR title follows Conventional Commits.
- CI must pass.
- Code review completed with at least 1 approval.
- All review comments addressed.

### QA
- PR merged to `develop`.
- Deployed to staging automatically via CI/CD.
- Acceptance criteria verified by QA or developer self-test.
- Any defects are fixed before marking Done.

### Done
- Acceptance criteria met.
- No known defects.
- Plane/issue tracker updated.
- Story closed.

---

## Definition of Ready (DoR)

A story is not started until ALL of the following are true:

- [ ] Title clearly describes the user value delivered.
- [ ] Acceptance criteria written and agreed with product owner.
- [ ] UI designs or mockups linked (if applicable).
- [ ] Dependencies on other stories or systems identified.
- [ ] Estimated (story points or T-shirt size).
- [ ] Assigned to a developer for the sprint.

---

## Definition of Done (DoD)

A story is not closed until ALL of the following are true:

- [ ] All acceptance criteria pass.
- [ ] Code reviewed and approved.
- [ ] All CI checks pass (build, tests, lint, security scan).
- [ ] No regression in existing tests.
- [ ] Deployed to staging.
- [ ] QA sign-off on staging.
- [ ] Documentation updated if public API or process changed.
- [ ] Ticket closed in issue tracker.

---

## Release Process

1. At end of sprint (or on demand), create `release/<version>` from `develop`.
2. Run regression tests on release branch.
3. Fix only critical bugs on the release branch — no new features.
4. Merge to `main` via PR.
5. Tag `main` with `v<version>`.
6. CI/CD deploys `main` to production automatically.
7. Merge release branch back to `develop`.
8. Communicate release notes to stakeholders.

---

## Hotfix Process

1. Identify and confirm the production defect.
2. Create `hotfix/<id>-description` from `main`.
3. Fix and test locally.
4. Open PR against `main`. Fast-track review (1 approval minimum).
5. Merge to `main`, tag with patch version, deploy.
6. Merge hotfix branch to `develop`.
7. Update ticket and notify stakeholders.

---

## Environment Strategy

| Environment | Branch | Deploy trigger | Purpose |
|---|---|---|---|
| `dev` | `develop` | Automatic on merge | Integration testing |
| `staging` | `develop` or `release/*` | Automatic on merge | QA, stakeholder demos |
| `production` | `main` | Automatic on tag | Live system |

- Configuration per environment via Azure App Configuration or environment-specific secrets.
- Never promote code that hasn't passed staging QA to production.

---

## BMAD Story Execution

When using AI-assisted development with BMAD:

1. Story file created by `bmad-create-story` skill — stored in `docs/stories/`.
2. Developer reviews story file and confirms it is Ready.
3. `bmad-dev-story` skill executes the story implementation.
4. `bmad-code-review` skill runs a structured adversarial code review.
5. Developer addresses all BLOCKER and MAJOR findings before opening PR.
6. Normal PR + QA + Done flow continues.

Story files are committed to the repo alongside the code they describe.

---

## What to Never Do

- Never merge a story that hasn't passed CI.
- Never deploy to production without staging QA.
- Never skip code review ("I'm the only dev" is not an exception).
- Never work on more than one story simultaneously.
- Never close a ticket without confirming acceptance criteria pass on staging.
- Never let a release branch live more than 3 days — stabilize fast and ship.
