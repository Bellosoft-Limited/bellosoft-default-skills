---
name: bellosoft-prd
description: >
  Interactive requirements gathering and PRD generation. Triggers when the user says
  /bellosoft-prd, "create a PRD", "write a PRD", "document requirements", "I have a feature
  to spec", "new feature", "product requirements", "write up this idea". Scans existing
  PRDs, asks if this is new or an amendment, gathers requirements through scored dialogue,
  and saves to docs/prd/YYYY-MM-DD-feature-name.md. Hands off to /bellosoft-plan-epics
  when done.
---

# Skill: bellosoft-prd

Interactive requirements gathering that produces a professional PRD ready for
`/bellosoft-plan-epics` to consume.

```
/bellosoft-prd                       ← start interactive session
/bellosoft-prd "feature description" ← start with initial context
/bellosoft-prd amend                 ← jump straight to amendment flow
```

---

## Step 1 — Scan existing PRDs

Before anything else, check what PRDs already exist:

```bash
find docs/prd/ -name "*.md" 2>/dev/null | sort -r | head -20
```

**If PRDs exist**, show them and ask:

```
Found existing PRDs:

  2026-05-15  campaign-scheduling
  2026-04-02  user-onboarding
  2026-03-18  billing-stripe

Is this a new PRD or an amendment to an existing one?
  1. New PRD
  2. Amend [feature name]  ← choose one from the list
```

**If no PRDs exist**, proceed directly to Step 2 as a new PRD.

---

## Step 2 — Amendment flow (if amending)

Load the existing PRD and ask:

```
Loaded: docs/prd/2026-05-15-campaign-scheduling.md
Current version: 1.0

What changed?
  1. Create new version file (v2) — keeps original intact, full history preserved
  2. Edit in place — update the existing file with a changelog section appended

Which would you prefer?
```

If **new version file**: proceed through full requirements flow, pre-populate from existing PRD, let the user describe what changed. Save as `docs/prd/YYYY-MM-DD-campaign-scheduling-v2.md`.

If **edit in place**: load existing PRD content, ask what changed, update only the affected sections, append a changelog entry at the bottom. Skip the full quality scoring flow — jump straight to edits.

---

## Step 3 — Gather project context (new PRD only)

Read in parallel to understand the codebase:
- `README.md`
- `package.json` or `*.csproj` or `pyproject.toml`
- `docs/plan/codebase-audit.md` (if exists — reveals tech stack, patterns, existing modules)

Present what was understood:

```
Here's what I understand about the project:
  Stack: [detected stack]
  Existing modules: [from audit if available]

And here's my initial understanding of what you want to build:
  [2-3 sentence interpretation of the feature request]

Is this correct? What would you like to add or correct?
```

---

## Step 4 — Quality Assessment

Evaluate the current state of requirements on a 100-point scale:

### Scoring dimensions

| Dimension | Points | What's needed |
|-----------|--------|---------------|
| Business Value & Goals | 30 | Problem statement, success metrics, ROI/outcomes |
| Functional Requirements | 25 | User stories with ACs, workflows, edge cases |
| User Experience | 20 | Personas, user journeys, UI constraints |
| Technical Constraints | 15 | Performance, security, integrations |
| Scope & Priorities | 10 | MVP definition, phasing, priority ranking |

Display after each round:

```
📊 Requirements Quality Score: [TOTAL]/100
  Business Value & Goals:    [X]/30
  Functional Requirements:   [X]/25
  User Experience:           [X]/20
  Technical Constraints:     [X]/15
  Scope & Priorities:        [X]/10

[If < 90]: Gaps in: [lowest scoring areas]. Let me ask a few questions...
[If ≥ 90]: Ready to generate PRD.
```

**Threshold: 90/100 required before generating the PRD.**

---

## Step 5 — Targeted clarification

If score < 90, ask 2-3 questions focused on the lowest-scoring dimension. Use the `AskUserQuestion` tool where possible to keep it interactive.

### Question bank by dimension

**Business Value (if <24/30):**
- What specific problem are we solving, and who feels the pain most?
- How will we know this was successful? What does good look like in 3 months?
- What's the cost of not building this?

**Functional Requirements (if <20/25):**
- Walk me through the main user workflow step by step.
- What should happen when [specific edge case or failure]?
- What's must-have vs. nice-to-have for the first release?

**User Experience (if <16/20):**
- Who are the primary users and what are their goals?
- What does the ideal interaction look like from the user's perspective?
- Are there any UI/UX constraints or existing design patterns to follow?

**Technical Constraints (if <12/15):**
- Any performance expectations (response times, scale, concurrent users)?
- Security or compliance requirements (auth, data privacy, GDPR, SOC2)?
- What systems or APIs does this need to integrate with?

**Scope & Priorities (if <8/10):**
- What's the minimum version that delivers real value?
- Should this be phased? What goes in phase 2?
- Of everything discussed, what are the top 3 priorities?

After each answer, recalculate and show the updated score with delta:
```
Updated score: 78/100 (+8)  Business Value improved from 18 → 26.
```

Repeat until 90+ or the user explicitly says "generate it anyway" (in which case note the gaps in the PRD).

---

## Step 6 — Determine filename

Before generating, derive a clean feature name from the title:
- Lowercase, hyphenated, max 4 words
- Examples: `campaign-scheduling`, `user-onboarding-v2`, `stripe-billing`

Confirm:
```
This PRD will be saved as:
  docs/prd/2026-06-03-campaign-scheduling.md

Correct? (yes / [suggest a different name])
```

Create `docs/prd/` if it doesn't exist.

---

## Step 7 — Generate PRD

Once confirmed, generate and save the PRD:

```markdown
# Product Requirements Document: [Feature Name]

**Version:** 1.0
**Date:** YYYY-MM-DD
**Status:** Draft
**Quality Score:** [SCORE]/100
**Author:** [leave blank — PM to fill]

---

## Executive Summary

[2-3 paragraphs: what problem this solves, who it helps, expected impact,
and why now.]

---

## Problem Statement

**Current situation:** [Pain points or limitations today]
**Proposed solution:** [High-level description]
**Business impact:** [Quantifiable or qualitative expected outcomes]

---

## Success Metrics

| Metric | Target | How measured |
|--------|--------|-------------|
| [KPI 1] | [value] | [method] |
| [KPI 2] | [value] | [method] |

**Validation timeline:** [When and how metrics will be reviewed]

---

## User Personas

### Primary: [Persona Name]
- **Role:** [User type]
- **Goals:** [What they want to achieve]
- **Pain points:** [Current frustrations]
- **Technical level:** Novice / Intermediate / Advanced

[Add secondary persona only if meaningfully different from primary]

---

## User Stories & Acceptance Criteria

### Story 1: [Story Title]
**As a** [persona], **I want to** [action] **so that** [benefit].

**Acceptance Criteria:**
- [ ] [Specific, testable criterion — happy path]
- [ ] [Edge case or error handling]
- [ ] [Performance or constraint criterion if applicable]

[Repeat for each core story — typically 3-5 for MVP]

---

## Functional Requirements

### [Feature 1 Name]
- **Description:** [What it does]
- **User flow:** [Step-by-step interaction]
- **Edge cases:** [What happens when X fails or Y is missing]
- **Error handling:** [How the system responds to failures]

[Repeat for each feature]

### Out of Scope
- [Explicitly list what is NOT in this release]
- [Prevents scope creep in plan-epics decomposition]

---

## Technical Constraints

### Performance
- [Response time requirements]
- [Scale / concurrency requirements]

### Security & Compliance
- [Auth / authorization requirements]
- [Data privacy, GDPR, SOC2, etc.]

### Integrations
| System | Purpose | Dependency |
|--------|---------|-----------|
| [System] | [why needed] | [blocking / non-blocking] |

### Stack Alignment
- [Required to use existing stack — reference codebase-audit if available]
- [Any new dependencies or infrastructure needed]

---

## MVP Scope & Phasing

### Phase 1 — MVP
- [Feature / story 1]
- [Feature / story 2]

**MVP definition:** [The minimum that delivers real user value]

### Phase 2 — Post-launch enhancements
- [Enhancement 1]
- [Enhancement 2]

### Future considerations
- [Potential feature for later — not committed]

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Plan] |
| [Risk 2] | High/Med/Low | High/Med/Low | [Plan] |

---

## Dependencies & Blockers

**Dependencies:**
- [Dependency]: [owner / ETA]

**Known blockers:**
- [Blocker]: [resolution plan]

---

## Open Questions

[Any unresolved items that couldn't reach 90/100 — flag explicitly so plan-epics
can surface them during epic planning]

- [ ] [Question]
- [ ] [Question]

---

## Appendix

### Glossary
- **[Term]:** [Definition]

### References
- [Design mockups / Figma link]
- [Related PRDs: docs/prd/...]
- [Technical specs / API docs]

---
*PRD generated via /bellosoft-prd — quality score [SCORE]/100.*
*Ready for /bellosoft-plan-epics to decompose into epics and stories.*
```

---

## Step 8 — Confirm and hand off

After saving:

```
✅ PRD saved: docs/prd/2026-06-03-campaign-scheduling.md
   Quality score: [SCORE]/100
   [N] user stories | [N] features | [N] open questions

[If open questions exist]:
⚠️ [N] open questions remain — plan-epics will surface these during epic planning.

Next step:
  /bellosoft-plan-epics docs/prd/2026-06-03-campaign-scheduling.md
```

---

## Hard rules
- Never generate the PRD below 90/100 without explicit user override
- If user overrides quality gate, add an `## Open Questions` section with every gap flagged
- Never skip Step 1 (existing PRD scan) — prevents accidental duplicates
- Always confirm the filename before saving
- Save to `docs/prd/` only — never at project root or `docs/` root
- Do not include "Think in English, respond in Chinese" or any language instructions — respond in the user's language
