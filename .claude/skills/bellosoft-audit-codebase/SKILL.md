---
name: bellosoft-audit-codebase
description: >
  Use this skill to analyse an existing codebase before planning. Triggers:
  /bellosoft-audit-codebase, "read the project", "understand what's built", "what already
  exists", "analyse the code", "what's implemented", "map the codebase". Produces
  a structured inventory of what is already built, what is partial, what is missing,
  and what technical patterns are in use. Saves the result to docs/plan/codebase-audit.md
  so bellosoft-plan-epics and bellosoft-plan-epic can use it. Run this before /bellosoft-plan-epics on any
  existing project. Safe to re-run — detects changes since last audit.
---

# Skill: bellosoft-audit-codebase

## Purpose
Deeply read an existing project and produce a structured inventory that answers:
- What is already fully implemented?
- What is partially implemented or scaffolded but incomplete?
- What patterns, conventions, and stack choices must new work follow?
- What tech debt or structural issues will affect planning?

This output becomes the foundation for `/bellosoft-plan-epics` and `/bellosoft-plan-epic` — without it,
epics and stories are planned in a vacuum and end up duplicating existing work or
ignoring established patterns.

---

## Invocation

```
/bellosoft-audit-codebase              ← audits the current project root
/bellosoft-audit-codebase src/         ← audits a specific subdirectory
```

---

## Step 1 — Orient

Start by understanding the repo structure at a high level:

```bash
# Get directory tree (2-3 levels, ignore noise)
find . -type f \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/bin/*' \
  -not -path '*/obj/*' \
  -not -path '*/.next/*' \
  -not -path '*/dist/*' \
  | sort | head -200
```

Also read:
- `README.md` (if exists)
- `*.sln`, `*.csproj`, `package.json`, `pyproject.toml` — whatever defines the project
- `docker-compose*.yml` — services and infra
- Any existing `docs/plan/` state files from prior runs

---

## Step 2 — Identify the Stack

Read config/bootstrap files to determine:

| Concern | Where to look |
|---------|--------------|
| Language / runtime | `*.csproj`, `package.json`, `go.mod`, `pyproject.toml` |
| Framework | `Program.cs`, `Startup.cs`, `main.ts`, `app.vue`, `nuxt.config.*` |
| Database | `appsettings*.json`, `docker-compose.yml`, migration folders |
| Auth | `Program.cs` DI registrations, `auth/`, `middleware/` |
| API style | Controllers folder, minimal API endpoints, GraphQL schema |
| Frontend | `src/views/`, `src/components/`, `src/pages/`, router file |
| Testing | `*.Tests.csproj`, `*.spec.ts`, `cypress/`, `playwright/` |
| CI/CD | `.github/workflows/`, `Dockerfile`, `dokploy.yml` |
| External integrations | `appsettings.json`, env vars, `HttpClient` registrations |

---

## Step 3 — Map Modules and Domains

Read enough of the code to identify the logical modules/domains:

For **.NET** projects:
- Read folder structure under `src/`
- Read each `*Service.cs`, `*Controller.cs`, `*Repository.cs` — just the class signature + public methods, not full bodies
- Read `DbContext` — all `DbSet<>` declarations reveal the data model
- Read any `*.cs` files in `Domain/`, `Entities/`, `Models/`

For **Vue/TS** projects:
- Read `src/router/index.ts` — all routes reveal all pages
- Read `src/stores/` — all Pinia/Vuex stores reveal all state domains
- Read `src/api/` or `src/services/` — all API calls reveal backend surface used
- Scan `src/components/` and `src/views/` — names reveal UI coverage

For **databases**:
- Read all migration files (just `Up()` method) — reveals full schema history
- Or read `DbContext` `OnModelCreating` — reveals current schema

---

## Step 4 — Classify Implementation Status

For each module/area discovered, classify:

| Status | Meaning |
|--------|---------|
| ✅ Complete | Implemented, has tests, used in production paths |
| 🔶 Partial | Scaffolded or started but missing key functionality |
| 🔲 Stub | Placeholder exists (empty class, TODO comment, route with no handler) |
| ❌ Missing | Referenced in config/types/routes but not implemented |
| ⚠️ Tech debt | Implemented but with known issues (hardcoded values, missing validation, no tests) |

Signals to look for:
- `// TODO`, `// FIXME`, `// HACK`, `throw new NotImplementedException()`
- Empty controller actions returning `Ok()` with no logic
- Routes defined in router but no corresponding view component
- `DbSet<>` in context with no migrations or no services referencing it
- Services registered in DI but never injected anywhere
- `.env.example` keys with no corresponding implementation

---

## Step 5 — Identify Conventions and Patterns

Document the patterns new code MUST follow:

```markdown
### Established Conventions

**API layer:**
- Route pattern: `/api/v1/{resource}`
- Auth: JWT via `[Authorize]` attribute, role claims in `ClaimTypes.Role`
- Response wrapper: `ApiResponse<T>` with `Success`, `Data`, `Errors`
- Validation: FluentValidation, registered in DI, called via pipeline

**Data layer:**
- ORM: EF Core with repository pattern (`IRepository<T>`)
- Migrations: `dotnet ef migrations add` in `Infrastructure` project
- Soft deletes: `IsDeleted` flag on all entities, global query filter applied
- Audit: `CreatedAt`, `UpdatedAt`, `CreatedBy` on all entities

**Frontend layer:**
- State: Pinia stores, one per domain
- API calls: `useApi()` composable, not raw fetch
- Forms: `vee-validate` + `zod` schemas
- Components: PascalCase, one file per component, no inline styles

**Testing:**
- Unit: xUnit, Moq for mocking, FluentAssertions
- Integration: `WebApplicationFactory<Program>`, test DB via `Respawn`
- Coverage threshold: 80% on service layer

**Error handling:**
- Global exception middleware returns RFC 7807 ProblemDetails
- Business errors: `DomainException` with error code
```

If a pattern is inconsistent across the codebase — note it:
```
⚠️ INCONSISTENCY: Some controllers use repository pattern, others query DbContext directly.
New code should use repository pattern.
```

---

## Step 6 — Produce the Audit Report

Output the full report and save to `docs/plan/codebase-audit.md`:

```markdown
# Codebase Audit — [Project Name]
**Audited:** [today's date]
**Root:** [path audited]
**Stack:** [e.g. .NET 10 / Vue 3 / PostgreSQL / Docker]

---

## Stack Summary
| Concern | Technology |
|---------|-----------|
| Backend | .NET 10, ASP.NET Core minimal API |
| Frontend | Vue 3, TypeScript, Pinia, Vite |
| Database | PostgreSQL 16, EF Core 9, pgvector |
| Auth | JWT, ASP.NET Core Identity |
| Testing | xUnit, Vitest, Playwright |
| Infra | Docker, Dokploy, Nginx |
| External | Evolution API (WhatsApp), Stripe, Mercado Pago |

---

## Module Inventory

| Module | Status | Notes |
|--------|--------|-------|
| Auth / Identity | ✅ Complete | JWT + refresh tokens, roles implemented |
| Contacts | ✅ Complete | CRUD, soft delete, audit fields |
| Messaging / WhatsApp | 🔶 Partial | Send works; receive webhook handler stubbed |
| Campaigns | 🔶 Partial | Create/list done; scheduling not wired to Hangfire |
| Billing / Stripe | 🔲 Stub | `StripeService.cs` exists, all methods throw NotImplementedException |
| Opt-out flow | ❌ Missing | Referenced in `ContactDto` but no handler, no DB column |
| Admin dashboard | 🔶 Partial | Stats page exists; charts hardcoded with mock data |
| User management | ✅ Complete | Invite, roles, deactivate all working |
| API rate limiting | ⚠️ Tech debt | Implemented but limit is hardcoded, not configurable per tenant |

---

## Data Model (current schema)

Key entities and their relationships:
- `Tenants` → `Users` (1:N)
- `Tenants` → `Contacts` (1:N, soft delete)
- `Contacts` → `Messages` (1:N)
- `Campaigns` → `CampaignContacts` (N:M via join table)
- `Subscriptions` → `Tenants` (1:1, nullable — billing not complete)

Missing tables (referenced in code but no migration):
- `OptOutLogs` — referenced in `ContactDto.OptedOutAt` but no table
- `WebhookEvents` — `IWebhookEventStore` interface exists but no implementation

---

## TODOs and Stubs Found

| File | Line | Content |
|------|------|---------|
| `StripeService.cs` | 23, 45, 67 | `throw new NotImplementedException()` |
| `CampaignScheduler.cs` | 89 | `// TODO: wire to Hangfire` |
| `src/views/Analytics.vue` | 15 | `// FIXME: replace mock data` |
| `WebhookController.cs` | 112 | Empty `Ok()` return — no logic |

---

## Established Conventions
[Filled from Step 5]

---

## Tech Debt Register

| Item | Severity | Impact on planning |
|------|----------|--------------------|
| Hardcoded rate limits | Medium | Any multi-tenant work needs this fixed first |
| Missing tests on service layer | High | New features must add tests; refactor sprint needed |
| DbContext queried directly in 3 controllers | Low | Follow repository pattern for new code |

---

## Recommendations for Planning

Based on this audit, before adding new features:
1. **Must fix first:** [any blocking tech debt]
2. **Complete before extending:** [partial modules that block new work]
3. **Safe to build on:** [stable modules new epics can depend on]
4. **Watch out for:** [gotchas, inconsistencies, known issues]
```

---

## Step 7 — Check for existing docs/plan/ state

If `docs/plan/epics.md` already exists, cross-reference:
- Are any planned epics already fully implemented? → Mark as ✅ Done
- Are any planned epics partially done? → Update status
- Are there implemented features NOT in any epic? → Flag as undocumented work

Output a reconciliation note if `docs/plan/` state exists:
```
## Reconciliation with existing plan

| Epic | Planned status | Actual status (from audit) |
|------|---------------|---------------------------|
| E1: Auth | ✅ Done (per plan) | ✅ Confirmed complete |
| E2: Campaigns | 🔲 Not started (per plan) | 🔶 Actually ~40% done |
| E3: Billing | 🔲 Not started (per plan) | 🔲 Stub only — confirms plan |
```

---

## Step 8 — Save and hand off

Save the report to `docs/plan/codebase-audit.md`.

Output:
```
✅ Audit complete. Saved to docs/plan/codebase-audit.md

Summary:
  ✅ Complete modules: N
  🔶 Partial modules: N
  ❌ Missing (referenced but absent): N
  ⚠️ Tech debt items: N

Next steps:
  /bellosoft-plan-epics [prd.md]   ← will use this audit automatically
  /bellosoft-plan-epic E1           ← will use this audit for conventions + status
```

---

## Hard rules
- Read actual code — do not guess or hallucinate implementations
- Never mark something ✅ Complete without reading the implementation
- Always check for TODOs and NotImplementedException
- Save to `docs/plan/codebase-audit.md` before finishing
- If codebase is too large to read fully, prioritise: DbContext → Services → Controllers → Router → Stores
