# Review Checklist
> Sources: Google Engineering Practices Code Review Guide, OWASP Code Review Guide v2, Microsoft PR Practices
> Use this checklist on every PR. Severity labels: 🔴 BLOCKER · 🟡 MAJOR · 🔵 MINOR · 💡 NIT

---

## PR Hygiene (author responsibility — check before requesting review)

- [ ] PR does one thing. Refactors are in a separate PR from feature changes.
- [ ] PR description explains **what** and **why**, not just what files changed.
- [ ] PR is linked to a story/issue.
- [ ] CI passes before review is requested.
- [ ] No merge conflicts.
- [ ] PR size is reasonable (~100–300 lines). If larger, a comment explains why.
- [ ] No debug code, `console.log`, `TODO` hacks, or commented-out code.
- [ ] No secrets, tokens, or connection strings committed.

---

## Design

- [ ] 🔴 The change belongs in this codebase, not in a library or separate service.
- [ ] 🔴 The change integrates cleanly with existing architecture and patterns.
- [ ] 🟡 No over-engineering — solves the current problem, not speculative future ones.
- [ ] 🟡 No functionality that isn't needed now is added.
- [ ] 🔵 Change is decomposed into the smallest meaningful unit.

---

## Functionality

- [ ] 🔴 The code does what the story/ticket describes.
- [ ] 🔴 All acceptance criteria are met.
- [ ] 🔴 No obvious logic bugs found by reading the code.
- [ ] 🔴 Edge cases are handled: null/empty input, zero, max values, invalid states.
- [ ] 🟡 Concurrent code (if any) is free of race conditions and deadlocks.
- [ ] 🟡 No silent failures — errors are surfaced appropriately.
- [ ] 🔵 UI changes (if any) look and behave correctly (reviewed in browser/screenshot).

---

## Security (treat all 🔴 as absolute blockers)

- [ ] 🔴 No SQL string concatenation. Parameterized queries or ORM only.
- [ ] 🔴 All external input is validated at system boundaries (API controllers, form handlers).
- [ ] 🔴 No sensitive data (passwords, tokens, PII) logged or returned in responses.
- [ ] 🔴 Authentication and authorization checks are present on new endpoints.
- [ ] 🔴 No hardcoded secrets, API keys, or credentials.
- [ ] 🔴 File upload paths are validated — no path traversal.
- [ ] 🔴 No deserialization of untrusted data without type constraints.
- [ ] 🟡 HTTP responses do not expose internal stack traces or error details.
- [ ] 🟡 CORS policies are not wildcarded for credentialed requests.
- [ ] 🟡 New dependencies are from trusted sources and are not known-vulnerable.
- [ ] 🔵 Least privilege: service accounts and roles have only required permissions.

---

## Tests

- [ ] 🔴 New logic has test coverage (unit or integration, as appropriate).
- [ ] 🔴 Tests actually test the behavior, not just that code runs without throwing.
- [ ] 🟡 Tests cover the happy path AND at least the main failure/edge case paths.
- [ ] 🟡 Test names describe what is being tested: `Should_ReturnNotFound_When_OrderDoesNotExist`.
- [ ] 🟡 No tests that always pass regardless of implementation changes (tautological tests).
- [ ] 🔵 Test setup is minimal — no unnecessary mocking of things not under test.
- [ ] 🔵 No test logic duplication that a helper or builder pattern could simplify.

---

## Code Quality

- [ ] 🟡 Code is readable without needing comments to understand what it does.
- [ ] 🟡 Method and class names clearly communicate intent (see `coding-standards.md`).
- [ ] 🟡 No method longer than ~30 lines without a strong reason.
- [ ] 🟡 No class with more than one responsibility.
- [ ] 🟡 No duplicate logic — shared logic is extracted appropriately.
- [ ] 🔵 Comments explain **why**, not **what**. If a comment explains what, simplify the code instead.
- [ ] 🔵 No dead code, unreachable branches, or unused variables/imports.
- [ ] 💡 NIT-level style issues (whitespace, naming preference) are prefixed with "Nit:" and non-blocking.

---

## Consistency

- [ ] 🟡 Code follows existing patterns in the codebase (error handling, logging, response shapes).
- [ ] 🟡 New abstractions match the style of existing ones (same level of granularity).
- [ ] 🔵 File and folder placement follows project structure conventions.
- [ ] 🔵 Coding standards from `coding-standards.md` are followed.

---

## Documentation

- [ ] 🟡 Public API changes include updated XML doc comments (`///` in C#) or JSDoc.
- [ ] 🔵 README or related docs updated if behavior, setup steps, or config changed.
- [ ] 🔵 Any existing TODO comments that are resolved are removed.

---

## Dependency Changes

- [ ] 🔴 New NuGet/npm packages are justified and approved (not added casually).
- [ ] 🟡 No packages with known CVEs at the version pinned.
- [ ] 🔵 Package versions are pinned or range-controlled.

---

## How to comment as a reviewer

| Prefix | Meaning |
|---|---|
| *(no prefix)* | Must fix before merge |
| `Nit:` | Optional polish — non-blocking |
| `Question:` | Seeking understanding, not requiring change |
| `Suggestion:` | Alternative worth considering, non-blocking |
| `Blocker:` | Cannot merge without resolving |

**Principles:**
- Technical facts and data override personal preferences.
- Style guide is the authority on style — personal preference is not a merge blocker.
- Approve when the PR improves code health overall, even if not perfect.
- Be specific: quote the line, state the concern, suggest the fix.
- Acknowledge good work. Reviews are not only for problems.

---

## PR size guidelines

| Lines changed | Signal |
|---|---|
| < 100 | Ideal — fast review, low risk |
| 100–300 | Normal — one focused concern |
| 300–600 | Needs justification — consider splitting |
| > 600 | Reject unless auto-generated or file deletion |
