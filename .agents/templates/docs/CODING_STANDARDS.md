# Coding Standards

How code in this repo should be written. Read during code review (`/code-review`), not before implementing.

## Shared Bellosoft standards

These files are part of this standard. Read each one that applies to the change under review:

- `.agents/core/coding-standards.md`: naming, structure and style for every stack
- `.agents/core/security-rules.md`: security rules
- `.agents/core/testing-patterns.md`: how tests are written
- `.agents/stack/<name>.md`: rules for each stack this project uses (`ls .agents/stack/`)

The sync script overwrites those files, so don't edit them here. Put project rules in the section below.

## Project-specific standards

Rules that apply only to this repo. When a rule here conflicts with a shared standard, the rule here wins.

Only add judgement calls, such as cross-file consistency or matching the surrounding style. If a linter, pre-commit hook or CI check could catch the problem, add that check instead of a rule.

<!-- Add project rules below. /retro proposes additions after a review misses something. -->
