# Load parent context

Walk up from the loaded ticket. Fetch with `/bellosoft-jira get [key]`.

| Loaded ticket | Fetch |
|---------------|-------|
| Task / Sub-task | Parent story (`parent` field), then its epic (`parent` or `Epic Link`) |
| Story | Parent epic |
| Epic | Nothing. Read `docs/planning-artifacts/epics.md` |

Also read `docs/planning-artifacts/epic-plans/E{N}-plan.md` if it exists.
It lists all stories and tasks of the epic.

## Extract

From the story:
- User story statement.
- All ACs. The plan must not break any of them.
- Technical notes and constraints.

From the epic:
- Epic goal.
- Conventions set for this epic.
- Other stories: what is done, what comes next.
- Dependencies on other stories.

## Output

Print nothing here. Use the data in the plan.
If a parent is missing, continue. Do not block the plan.
