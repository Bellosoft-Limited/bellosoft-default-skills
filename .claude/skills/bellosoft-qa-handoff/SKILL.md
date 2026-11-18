---
name: bellosoft-qa-handoff
description: "After raising a PR, post a QA handoff comment on the Jira ticket: what changed, how to test it, and the risk."
disable-model-invocation: true
---

# QA handoff

Post one Jira comment that the developer follows to smoke-test the change and QA follows to verify it: the same steps for both. The comment has exactly three sections: **What changed**, **How to test**, **Risk**.

Every Jira operation goes through the `bellosoft-jira` skill.

## Steps

1. **Find the ticket.** Use the key passed as an argument. Otherwise take it from the open PR's title, which starts with `#<KEY>` (`gh pr view --json title,url,body,baseRefName`), then from the branch name. If nothing resolves, ask. Done when you hold a key and know whether a PR exists.

2. **Read the requirement.** `bellosoft-jira get <KEY>`. Check `board_type` in `docs/planning-artifacts/jira-profile.md`:
   - **Scrum**: the key is usually a Sub-task or Sub-bug. Also get its parent User Story, which holds the acceptance criteria, and find the story's QA Sub-task: `bellosoft-jira search "parent = <STORY> AND summary ~ 'QA:'"`.
   - **Kanban**: the Task or Bug holds the acceptance criteria itself.

   Done when you hold every acceptance criterion the change is meant to satisfy.

3. **Read the change.** The PR body if there is one (its Summary and Merge Danger sections feed **What changed** and **Risk**), plus `git diff <base>...HEAD`, where base is the PR's base branch or else the repo's default branch. Done when every acceptance criterion maps to behaviour in the diff, or you have noted the ones that don't.

4. **Draft the comment** from the template below, in the language the ticket is written in, using the project's `GLOSSARY.md` vocabulary.

5. **Confirm.** Show the draft to the developer, flagging any acceptance criterion with no matching change. Post only once they approve or edit it.

6. **Post.**
   - **Scrum**: on the QA Sub-task, plus a one-line pointer on the development item (`QA handoff posted on <QA-KEY>`). No QA Sub-task → on the development item.
   - **Kanban**: on the Task or Bug.

   Statuses stay as they are: Jira automation and the team move tickets.

**Follow-up fixes** (e.g. QA sent the ticket back): run again and post a new comment headed `QA handoff (update)`, covering only what changed since the previous handoff.

## Template

```markdown
**QA handoff** · PR: <url, or "not raised yet">

### What changed
- <behaviour a user or tester can observe, one bullet per change>

### How to test
**Before you start:** <environment, test data, users and roles, feature flags, migrations to run>

1. <action> → **Expected:** <observable result> _(AC 1)_
2. <action> → **Expected:** <observable result> _(AC 2)_

### Risk
- **Could affect:** <screens, flows or integrations near the change that deserve a regression check>
- **Rollback:** <easy: revert the PR | hard, and why: data migration, external calls, emails or messages sent>
```

- **What changed** describes behaviour in the words QA uses. Name a file, setting or endpoint only when the tester has to touch it.
- **How to test** gives every acceptance criterion at least one numbered scenario, tagged with the criterion it proves, plus the edge cases and failure paths the diff handles. Every step is something a tester can do in the QA environment; every expected result is something they can see.
- **Risk** names concrete areas, never generic warnings.
- The comment is a manual verification guide. Automated test evidence lives in the PR body, through the `pr` skill.
