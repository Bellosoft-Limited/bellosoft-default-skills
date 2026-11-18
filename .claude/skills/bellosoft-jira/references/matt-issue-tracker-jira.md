# Issue tracker: Jira (Bellosoft)

Issues and specs for this repo live in Jira. **Every Jira operation goes through the `bellosoft-jira` skill**; never call Atlassian MCP tools or the REST API directly. `bellosoft-jira` resolves credentials, the project key (`docs/planning-artifacts/status.md` → `jira_project_key`), the board type, issue types and custom field IDs.

<!-- Seed: .claude/skills/bellosoft-jira/references/matt-issue-tracker-jira.md. This copy is yours: edit it to match this project's Jira workflow. -->

## Board type decides the issue types

Read `board_type` from `docs/planning-artifacts/jira-profile.md` (`bellosoft-jira` detects it during setup). Use only these types:

| Board | Issue types | Hierarchy |
|---|---|---|
| **Scrum** | Epic, User Story, Sub-task, Sub-bug | Epic → User Story → Sub-task / Sub-bug |
| **Kanban** | Task, Bug | None. Tasks and Bugs never have child issues |

Never create any other type, and never give a Task or Bug a child.

## Conventions

- **No estimates.** Don't set story points or time tracking. Leave them empty unless the user gives a value.
- **No sprints.** New issues go to the backlog. Assign a sprint only when the user asks.
- **Create a top-level issue** (Epic, User Story, Task, Bug): `bellosoft-jira create-epic` / `create-story issue_type=<type>`. Pass the body as markdown; `bellosoft-jira` converts it to ADF. Never summarise the body.
- **Create a child issue** (Sub-task, Sub-bug, Scrum only): `bellosoft-jira create-task issue_type=<Sub-task|Sub-bug> parent=<User Story key>`.
- **Read an issue**: `bellosoft-jira get <KEY>` (summary, description, labels, status, links, comments).
- **List issues**: `bellosoft-jira search "<JQL>"`, e.g. `labels = needs-triage AND statusCategory != Done ORDER BY created ASC`.
- **Blocking**: Jira's native **Blocks** link (`<blocker> blocks <blocked>`), via `bellosoft-jira link <blocker> blocks <blocked>`. Link top-level issues only (User Stories on Scrum, Tasks/Bugs on Kanban), never Sub-tasks.
- **Unblocked**: a ticket is unblocked when every issue it "is blocked by" is in **In Review**, **Ready for QA**, **Ready to Release** or **Done**, i.e. anywhere past In Progress. A blocker doesn't have to be released, only handed off for review. A blocker labelled `wont-do` follows the same rule: once it's past In Progress, it no longer blocks.
- **Count open blockers**: `bellosoft-jira search "issue in linkedIssues(<KEY>, 'is blocked by') AND status NOT IN ('In Review', 'Ready for QA', 'Ready to Release', 'Done')"`; the result count is the number of open blockers (0 means startable).
- **Comment on an issue**: `bellosoft-jira update <KEY> comment "..."`.
- **Apply / remove labels**: `bellosoft-jira update <KEY> label add <label>` / `label remove <label>`.
- **Close**: post the explanation as a comment, then `bellosoft-jira update <KEY> transition "Done"`. Only close after the user has confirmed, as the skills' flows already do.
- **Won't do**: there is no "Won't Do" status. Post the reason as a comment, add the label `wont-do`, then transition to Done. The triage role `wontfix` is this same `wont-do` label (see `docs/agents/triage-labels.md`).

## How work is closed

Work closes through pull requests. The key in them is the **development item** the PR delivers (Sub-task or Sub-bug on Scrum, Task or Bug on Kanban).

- **Branch**: the developer creates the working branch by hand before starting. Skills work on the current branch; `/mattpocock-skills:implement-spec` uses it as its integration branch.
- **PR title**: `#<KEY>: <title>`, e.g. `#PROJ-42: Throttle repeated login attempts`. Jira automation reads the key and moves the item to **In Review** when the PR is raised, so never transition it yourself.
- **Whole-Epic PR** (`/mattpocock-skills:implement-spec`): the title carries the **Epic** key, e.g. `#PROJ-40: Login hardening`. Automation doesn't fire for an Epic, so the developer moves the Epic's items on the board by hand.
- **PR body**: the `mattpocock-skills:pr` skill.
- **After the PR**: the developer runs `/bellosoft-qa-handoff` to post testing steps on Jira.

**Ready for QA**, **Ready to Release** and **Done** belong to the team.

When a skill says "resolve the ticket the way the tracker closes work", raise the PR(s) and stop there.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Pull requests live on GitHub, issues in Jira.)_

## When a skill says "publish to the issue tracker"

### Scrum board

- A **spec** (`/mattpocock-skills:to-spec`): an **Epic**. Summary = spec title, description = full spec body.
- A **ticket** (`/mattpocock-skills:to-tickets`): a **User Story** under the spec's Epic, holding the ticket's full body (what to build, acceptance criteria). Blocking edges go between User Stories. Then break each User Story into child items:
  - **Development**: one **Sub-task** per separable piece of work (e.g. a backend part and a frontend part that different people would pick up), or a **Sub-bug** when the work fixes a defect. A small User Story gets a single development Sub-task or Sub-bug. Don't split for the sake of it.
  - **QA**: always one **Sub-task** titled `QA: <User Story title>`, with the User Story's acceptance criteria as the test checklist.

  Show the planned child items under each ticket when you present the breakdown for approval, so the user approves them too.
- A **ticket** from `/mattpocock-skills:triage`: a defect in an existing User Story becomes a **Sub-bug** under it. Anything else becomes a **User Story** with its development and QA children as above.

### Kanban board

- A **spec** (`/mattpocock-skills:to-spec`): a single **Task** holding the full spec body. A spec on a Kanban board is usually a huge Task, so **before creating it, ask the user whether this is the right board**: work that needs a spec usually belongs on a Scrum board, where it can be split into User Stories. Create the Task only if they confirm.
- A **ticket** (`/mattpocock-skills:to-tickets`, `/mattpocock-skills:triage`): one **Task**, or one **Bug** for a defect. No QA item: Kanban boards already have a fixed QA task.
- `/mattpocock-skills:to-tickets` on a spec Task: a Task never has children, so the spec Task is the unit of work. Don't split it into more Tasks; if the user wants it split, suggest moving the work to a Scrum board.

Publish blockers first so later tickets can link to real keys.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above. A Jira URL works too; `bellosoft-jira` extracts the key. On Scrum, read the User Story's Sub-tasks too.

## Wayfinding operations

Used by `/mattpocock-skills:wayfinder`. Wayfinder tickets are decisions (research, prototype, grilling, task), not development work, so they never get development or QA children.

Jira labels can't hold the `:` the skill uses, so `wayfinder:<type>` maps to the label `wayfinder-<type>` (`research`/`prototype`/`grilling`/`task`).

**Scrum board**

- **Map**: an Epic labelled `wayfinder-map`, holding the Notes / Decisions-so-far / Fog body.
- **Child ticket**: a User Story under the map Epic, labelled `wayfinder-<type>`.
- **Frontier query**: `bellosoft-jira search "parent = <MAP> AND statusCategory = 'To Do' AND assignee is EMPTY ORDER BY rank ASC"`, then drop any ticket with an open blocker (see **Count open blockers**); first in rank order wins.
- **Resolve**: comment the answer, transition the ticket to Done, then append a context pointer (gist + key) to the map's Decisions-so-far with `bellosoft-jira update <MAP> edit description`.

**Kanban board**

Work big enough for `/mattpocock-skills:wayfinder` rarely belongs on a Kanban board: before creating the map, ask the user whether this is the right board, as for a spec.

- **Map**: a single Task labelled `wayfinder-map`, holding the Notes / Decisions-so-far / Fog body.
- **Child ticket**: a Task labelled `wayfinder-<type>` and `wayfinder-<MAP-KEY>` (e.g. `wayfinder-PROJ-12`), with a `Map: <MAP-KEY>` line at the top of the body. Tasks never have children, so the label, not a parent, ties tickets to their map.
- **Frontier query**: `bellosoft-jira search "labels = wayfinder-<MAP-KEY> AND statusCategory = 'To Do' AND assignee is EMPTY ORDER BY rank ASC"`, then drop any ticket with an open blocker; first in rank order wins.
- **Resolve**: comment the answer, transition the ticket to Done, then append a context pointer (gist + key) to the map's Decisions-so-far with `bellosoft-jira update <MAP> edit description`.

**Both boards**

- **Blocking**: see **Blocking** under Conventions.
- **Claim**: `bellosoft-jira update <KEY> assign me`, the session's first write. Once claimed, the ticket stays assigned to the driving dev.
