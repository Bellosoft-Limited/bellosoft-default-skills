---
name: bellosoft-dev-plan
description: >
  Invoked when the developer wants AI help planning a story before coding. Use this skill
  when the user types /bellosoft-dev-plan, mentions a story ID (PROJ-123, NOKEY-42),
  a story file path (.md), or says "start story", "plan this story", "help me implement STORY-123".
  Accepts a local .md file, a Jira ticket ID, a Plane ticket ID, or pasted story content.
  Produces a structured implementation plan with TDD approach — test cases listed BEFORE
  implementation steps. Waits for explicit approval before any code is written.
  THIS SKILL IS OPTIONAL — devs can work directly from Jira/Plane without it.
  Do NOT auto-invoke on general coding tasks.
---

# Skill: bellosoft-dev-plan

## Philosophy — skills are optional

This skill helps when a developer wants AI assistance planning their approach.
It is **not a gate**. Developers can and should:
- Work directly from the Jira or Plane ticket without this skill
- Start coding immediately without a plan
- Use only some skills (e.g. just `/bellosoft-dev-review` at the end)
- Skip AI entirely for straightforward stories

Use this skill when the story is complex enough that thinking through the
approach upfront is worth the time investment.

---

## Invocation

```
/bellosoft-dev-plan PROJ-123                        ← fetch from Jira by ticket ID
/bellosoft-dev-plan NOKEY-42                        ← fetch from Plane by ticket ID
/bellosoft-dev-plan https://org.atlassian.net/...   ← paste a full Jira URL — ID is extracted
/bellosoft-dev-plan path/to/story.md                ← load from local file
/bellosoft-dev-plan "add password reset to login"   ← typed free-form description
/bellosoft-dev-plan                                 ← paste story content, or find most recent .md
```

---

## Step 0.5 — Tracker resolution (first-time only)

Before fetching or creating any ticket:
- If `docs/planning-artifacts/status.md` contains `tracker:` → skip this step
- If not → load and follow `.claude/skills/bellosoft-plane/references/tracker-bootstrap.md`

---

## Step 1 — Load the Story

Determine the input type and load accordingly:

### A) Jira ticket ID or URL
Detect:
- Plain ticket ID: matches pattern `[A-Z]+-\d+` (e.g. `AP-29`, `PROJ-123`)
- Full Jira URL: contains `atlassian.net` or `jira` — extract ticket ID from URL:
  - `?selectedIssue=AP-29` → `AP-29`
  - `/browse/AP-29` → `AP-29`
  - Find first `[A-Z]+-\d+` match in the URL string

Check tracker from `docs/planning-artifacts/status.md`. If `tracker: jira`:
Delegate to `/bellosoft-jira get [issue_key]`.

The bellosoft-jira GET operation handles MCP and REST fallback automatically —
**do not show a "no connection" error here**; let the jira skill resolve it.

If tracker check needed and not yet configured, follow Step 0.5 first.

### B) Plane ticket ID (e.g. `NOKEY-42`, `BEL-7`)
Detect: matches Plane sequence number pattern or explicit Plane URL.

Delegate to `/bellosoft-plane`:
```
/bellosoft-plane get [sequence_number]
```
bellosoft-plane returns a structured story object (title, ACs, description).
If bellosoft-plane cannot connect → fall back: ask user to paste content.

### C) Local .md file path
Read the file directly. If missing, stop and ask for correct path.

### D) No argument given
1. Check for most recently modified `.md` under `docs/stories/`, `stories/`, `.plane/`
2. If found → confirm: "Found `stories/E1-S2-auth-login.md` — use this? (yes/no)"
3. If not found → ask: "Please provide a ticket ID, file path, or paste the story content."

### E) Pasted content
If the user pastes raw text (multi-line, structured) → use it directly.

### F) Typed free-form description
If the argument is a short natural-language phrase (not a ticket ID, path, or structured content):
- Use it as the story title and goal
- Ask the developer to define acceptance criteria before proceeding:

```
Got it — planning: "add password reset to login"

Before I can produce a plan, I need at least one acceptance criterion.
What does done look like? (e.g. "user receives a reset email and can set a new password")

You can:
  - Type the ACs here
  - Or I'll draft some based on the description and you confirm them
```

Draft ACs if the user asks, confirm them.

Then ask:
```
Should I create a ticket for this in your tracker before planning?
  1. Yes — create in Jira
  2. Yes — create in Plane
  3. No — plan only, I'll create the ticket manually (or not at all)
```

Only show options for trackers configured in `docs/planning-artifacts/status.md`. If `tracker: none` or no status file, skip this prompt and proceed to Step 2.

For Jira → delegate to `/bellosoft-jira create-story`.
For Plane → delegate to `/bellosoft-plane create-story`.

If the user chooses 1 or 2 — create the ticket (Story type) with the title, goal, and confirmed ACs, save the returned ticket ID, then proceed to Step 2 using that ticket as the story source. This way the plan is linked to a real ticket from the start.

---

After loading, extract and confirm:
- **Title / ID**
- **Goal** (what business value this delivers)
- **Acceptance Criteria** (numbered list)
- **Technical Notes** (any hints about files, APIs, patterns)
- **Out of Scope** (explicit exclusions)

If ACs are missing or ambiguous, flag them before proceeding:
```
⚠️ This story has no acceptance criteria. Proceeding without them means
the implementation plan will have no verifiable completion signal.
Continue anyway? (yes / define ACs first)
```

---

## Step 2 — Analyse the Codebase

**If `docs/planning-artifacts/codebase-audit.md` exists**, load it first:
- Read the Module Inventory to find which modules this story touches
- Read Established Conventions — all new code MUST follow them
- Read the Tech Debt Register for anything that affects this story
- Skip fresh codebase reading for modules already documented in the audit

**If no audit exists**, do a targeted read of the relevant code:
- Find existing files/modules most likely touched by this story (use `Glob`, `Grep`, `Read`)
- Identify the testing framework in use (xUnit, NUnit, Jest, Vitest, etc.)
- Identify naming conventions for test files (e.g. `*.Tests.cs`, `*.spec.ts`)
- Note any existing similar implementations to follow as patterns

If the audit exists but is stale (> 14 days old or story touches modules not covered),
note it and do a targeted re-read of only the affected files.

---

## Step 3 — Produce the Implementation Plan

Output a structured plan in this exact format:

```
## Implementation Plan — [STORY-ID]: [Title]

### Summary
[2-3 sentences explaining what will be built and why]

### Files to Create
- `path/to/new/file` — [purpose]

### Files to Modify
- `path/to/existing/file` — [what changes and why]

### Test Cases (write these FIRST)
For each acceptance criterion, list the test(s) that prove it:

| # | Test Name | Criterion Covered | Expected Behaviour |
|---|-----------|-------------------|--------------------|
| 1 | `ShouldDoX_WhenY` | AC-1 | ... |
| 2 | `ShouldFailWith_WhenZ` | AC-2 | ... |

### Implementation Steps
Only after all tests above are written and confirmed failing:

1. [Step — specific, max 1 file per step where possible]
2. ...

### Out of Scope (not touching)
- [item]

### Risks / Questions
- [Any ambiguity that needs clarification before starting]
```

---

## Step 4 — Wait for Approval

After outputting the plan, always end with:

```
---
Plan ready. Reply with:
  ✅ approve       — proceed to /bellosoft-dev-execute
  ✏️  [feedback]   — adjust the plan
  ❌ cancel        — abort (you can start coding directly without this plan)
```

**Do NOT write any code until the developer explicitly approves.**
