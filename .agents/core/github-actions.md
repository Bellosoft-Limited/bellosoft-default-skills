# GitHub Actions Guidelines
> Sources: GitHub Actions Security Hardening Guide, GitHub Docs
> Stack: GitHub Actions · Azure OIDC · Dependabot

---

## Workflow Structure

- Store all workflows in `.github/workflows/`.
- Use descriptive file names that reflect the trigger and purpose: `ci.yml`, `deploy-prod.yml`, `pr-checks.yml`.
- One workflow per concern. Do not put CI + deployment in a single workflow file.
- Use `name:` at the top of every workflow and every job.
- Use `on: pull_request` for CI checks, `on: push: branches: [main]` for deployments.

---

## Permissions (GITHUB_TOKEN)

- Set default `GITHUB_TOKEN` permissions to read-only at the workflow level:
  ```yaml
  permissions:
    contents: read
  ```
- Grant only the specific permissions each job needs:
  ```yaml
  jobs:
    deploy:
      permissions:
        contents: read
        id-token: write  # required for OIDC
  ```
- Never grant `write-all` unless absolutely necessary.
- Prevent workflows from creating or approving PRs unless explicitly required.

---

## Secrets Management

- Store all secrets in GitHub Secrets (repository or environment level) — never in workflow files.
- Never echo secrets to logs. Never print them with `echo "$SECRET"`.
- Do not use structured data (JSON blobs) as a single secret — create individual secrets per value.
- For derived secrets generated during a workflow, register them with `::add-mask::VALUE`.
- Use **environment-level secrets** with required reviewers for production deployments.
- Audit secrets regularly. Remove secrets no longer in use.
- Rotate secrets on a schedule and immediately after any suspected exposure.

---

## Cloud Authentication (Azure)

- Use **OIDC (OpenID Connect)** to authenticate to Azure from GitHub Actions — never store long-lived Azure credentials as secrets.
- Configure a Federated Credential on the Azure Managed Identity scoped to the specific repository and branch/environment.
- Required permissions for OIDC: `id-token: write` on the job.

```yaml
- name: Azure Login
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

- Scope federated credentials to the environment: `repo:org/repo:environment:production` — not `repo:org/repo:ref:refs/heads/main`.

---

## Third-Party Actions

- Pin all third-party actions to a **full commit SHA** — not a mutable tag:
  ```yaml
  # Good
  uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
  # Bad
  uses: actions/checkout@v4
  ```
- Only use actions from trusted sources (GitHub's own, or verified marketplace publishers).
- Review the source code of any third-party action before using it.
- Enable Dependabot for GitHub Actions to receive security updates automatically (`.github/dependabot.yml`):
  ```yaml
  version: 2
  updates:
    - package-ecosystem: github-actions
      directory: /
      schedule:
        interval: weekly
  ```

---

## Script Injection Prevention

- Never interpolate `github.event` values directly into `run:` shell scripts:
  ```yaml
  # Bad — injectable
  run: echo "${{ github.event.pull_request.title }}"

  # Good — use env var
  env:
    TITLE: ${{ github.event.pull_request.title }}
  run: echo "$TITLE"
  ```
- Prefer using a dedicated action (JavaScript/composite) over inline shell scripts when processing untrusted event data.
- Always quote shell variables: `"$VAR"` not `$VAR`.

---

## CI Workflow (Standard Pattern)

Every project should have a CI workflow triggered on `pull_request` that runs:

1. **Build** — compile/type-check
2. **Lint** — code style validation
3. **Tests** — unit + integration
4. **Security scan** — `dotnet list package --vulnerable`, `npm audit`, or CodeQL

```yaml
on:
  pull_request:
    branches: [develop, main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - name: Build
        run: dotnet build
      - name: Test
        run: dotnet test --no-build
```

- Require all CI checks to pass before PR merge (enforce via branch protection rules).
- Do not skip tests with `--no-test` flags in CI.

---

## Deployment Workflow (Standard Pattern)

- Trigger production deployment only on push to `main` (after PR merge).
- Use GitHub Environments with required reviewers for production.
- Run deployment to staging automatically; require manual approval for production.
- Never auto-deploy to production on PR merge without a staging gate.

```yaml
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    environment: staging
    # ...

  deploy-prod:
    environment: production  # configured with required reviewers
    needs: deploy-staging
    # ...
```

---

## Branch Protection

Configure on `main` and `develop`:

- Require status checks to pass before merging.
- Require at least 1 (main: 2) pull request review.
- Dismiss stale reviews on new pushes.
- Require branches to be up to date before merging.
- Do not allow bypassing the above settings (even for admins in production).
- Restrict who can push directly to `main`.

---

## CODEOWNERS

- Add `.github/CODEOWNERS` to require team review for sensitive changes:
  ```
  # Require review for workflow changes
  .github/workflows/ @bellosoft/devops-team

  # Require review for security-sensitive files
  src/auth/ @bellosoft/security-team
  ```
- All changes to workflow files require approval from a designated reviewer.

---

## Caching and Artifacts

- Cache dependencies to speed up builds:
  ```yaml
  - uses: actions/cache@<sha>
    with:
      path: ~/.nuget/packages
      key: ${{ runner.os }}-nuget-${{ hashFiles('**/*.csproj') }}
  ```
- Do not cache secrets or sensitive outputs.
- Upload build artifacts only if needed for downstream jobs or debugging.
- Set artifact retention to the minimum needed (default is 90 days — reduce for large artifacts).

---

## Self-Hosted Runners

- Prefer GitHub-hosted runners for all CI. Use self-hosted only when required by network access or performance.
- Never use self-hosted runners on public repositories.
- Use ephemeral (JIT) self-hosted runners to prevent persistent compromise.
- Isolate self-hosted runners — do not share them across environments (dev/staging/prod).

---

## What to Never Do

- Never store cloud credentials as GitHub secrets — use OIDC.
- Never pin actions to mutable tags (`@v4`, `@main`) — use commit SHAs.
- Never interpolate `github.event` values directly into `run:` commands.
- Never echo secrets to logs or output them in workflow steps.
- Never use self-hosted runners on public repos.
- Never deploy to production without a staging gate and required reviewer approval.
- Never grant `write-all` permissions to a workflow.
- Never commit `.env` files or secrets into the repo, even temporarily.
