# Azure Guidelines
> Sources: Microsoft Cloud Adoption Framework, Azure Security Best Practices, Microsoft SFI
> Stack: Azure PaaS · Azure SQL · App Service · Container Apps · Key Vault · Managed Identity

---

## Resource Naming Convention

Format: `<resource-type>-<workload>-<environment>-<region>-<instance>`

| Component | Values | Example |
|---|---|---|
| Resource type | Abbreviation (see below) | `app`, `rg`, `sqldb` |
| Workload | App or project name | `myproject`, `navigator` |
| Environment | `prod`, `dev`, `staging`, `test` | `prod` |
| Region | Short region code (optional) | `eastus2`, `westeu` |
| Instance | 3-digit number when multiple instances exist | `001` |

### Common Abbreviations

| Resource | Prefix |
|---|---|
| Resource group | `rg-` |
| App Service / Web App | `app-` |
| Function App | `func-` |
| Azure SQL Database | `sqldb-` |
| Azure SQL Server | `sql-` |
| Key Vault | `kv-` |
| Storage Account | `st` (no hyphen, all lowercase) |
| Container Registry | `cr` (no hyphen) |
| Container App | `ca-` |
| Container App Environment | `cae-` |
| Service Bus namespace | `sbns-` |
| API Management | `apim-` |
| Managed Identity | `id-` |
| Virtual Network | `vnet-` |
| Application Insights | `appi-` |
| Log Analytics Workspace | `log-` |
| Redis Cache | `redis-` |
| Cosmos DB | `cosmos-` |

Examples:
- `rg-myapp-prod` — resource group
- `app-myapp-prod-001` — App Service
- `sqldb-myapp-prod` — SQL Database
- `kv-myapp-prod` — Key Vault
- `stmyapp001` — Storage Account (no hyphens allowed)

Rules:
- Lowercase only. Hyphens as separators (except storage accounts and container registries where hyphens are not allowed).
- Names must be stable — they are hard to rename. Do not include info that will change (e.g. team names, versions).
- Global-scope resources (App Service, Storage, Key Vault, Container Registry) require globally unique names — include a short project code to ensure uniqueness.

---

## Tagging

All resources must have these tags:

| Tag | Purpose | Example |
|---|---|---|
| `Environment` | Distinguish prod/staging/dev | `prod`, `dev` |
| `Project` | Project or workload name | `myapp` |
| `Owner` | Team or person responsible | `backend-team` |
| `CostCenter` | Billing allocation | `engineering` |
| `ManagedBy` | Who provisioned it | `terraform`, `bicep`, `manual` |

- Apply tags at the resource group level. Resources inherit tags from their group via Azure Policy.
- Tag all resources. Untagged resources block cost attribution.

---

## Resource Groups

- One resource group per environment per workload: `rg-myapp-prod`, `rg-myapp-dev`.
- Do not mix environments in a single resource group.
- Do not use the default resource group.
- Apply delete locks on production resource groups: `CanNotDelete`.
- Group resources that share the same lifecycle together.

---

## Identity and Access Management

- Use **Managed Identity** for all service-to-service authentication within Azure. Never use connection strings with credentials.
- Assign managed identities at the most specific scope (resource level, not subscription level).
- Use **System-assigned Managed Identity** for resources with a 1:1 relationship to their identity.
- Use **User-assigned Managed Identity** for shared identity across multiple resources.
- Apply the principle of least privilege for all RBAC assignments.
- Never assign `Owner` or `Contributor` at the subscription level for application service identities.
- Audit all privileged role assignments. Review and remove unused assignments quarterly.
- Use Microsoft Entra ID (formerly Azure AD) for all authentication — never local accounts on shared resources.
- Enable MFA for all human accounts with Azure access.

---

## Secrets and Key Management

- Store all secrets, connection strings, API keys, and certificates in **Azure Key Vault**.
- Never store secrets in app settings, environment variables committed to source, or code.
- Applications access Key Vault via Managed Identity — never via a client secret.
- Enable soft delete and purge protection on all Key Vaults.
- Use Key Vault references in App Service / Container Apps (`@Microsoft.KeyVault(...)`) — do not copy secrets out of Key Vault into app config.
- Rotate secrets and certificates before expiry. Configure alerts on Key Vault expiration events.
- Separate Key Vaults per environment: `kv-myapp-prod`, `kv-myapp-dev`.

---

## App Service and Container Apps

- Use **App Service** for traditional web apps and APIs. Use **Container Apps** for microservices, event-driven workloads, and containerized APIs.
- Enable **Always On** for App Service apps that receive traffic (prevents cold starts).
- Use deployment slots (`staging` slot) for zero-downtime deployments with swap.
- Enforce HTTPS only. Disable HTTP.
- Set the minimum TLS version to 1.2.
- Enable health check endpoints and configure them on App Service.
- Store configuration in Azure App Configuration (not hard-coded in app settings).
- Use **VNet Integration** for apps that need to access private resources (SQL, Key Vault with private endpoint).

---

## Azure SQL Database

- Use the **vCore** pricing model for production (predictable performance, reserved capacity).
- Enable **Automatic Tuning** and review recommendations before accepting (don't blindly apply all suggestions).
- Enable **Transparent Data Encryption** (TDE) — on by default for Azure SQL, verify it's not disabled.
- Use **Azure Defender for SQL** (Advanced Data Security) in production.
- Restrict access: disable public endpoint in production, use private endpoint or VNet service endpoint.
- Use least-privilege accounts: application DB user gets only DML permissions on required tables.
- Enable threat detection and configure alerts for anomalous queries.
- Use geo-redundant backups. Test restore procedures regularly.

---

## Monitoring and Observability

- All production resources must emit logs and metrics to **Log Analytics Workspace**.
- All application code must use **Application Insights** — structured logging, request tracking, dependencies, exceptions.
- Set up alerts for: error rate spikes, high CPU/memory, HTTP 5xx responses, response time P95 > threshold.
- Use **Azure Monitor Workbooks** for operational dashboards.
- Retain logs for at minimum 90 days in Log Analytics. Archive to Storage for compliance if required.
- Configure Application Insights sampling for high-traffic apps to control costs (100% in dev, adaptive in prod).

---

## Networking

- Use **VNet** for all production environments. Do not put production services on the public internet without a firewall or gateway.
- Use **private endpoints** for Azure SQL, Key Vault, Storage, and Service Bus in production.
- Use **Application Gateway** or **Azure Front Door** as the public entry point for web apps — not direct App Service exposure.
- Apply **Network Security Groups** (NSGs) at the subnet level. Default: deny all inbound, allow only required traffic.
- Never open port 1433 (SQL Server) to the public internet.
- Use **Azure DDoS Protection Standard** for internet-facing workloads.

---

## Cost Management

- Review Azure Cost Management + Billing weekly during active development.
- Tag everything — cost analysis requires consistent tags.
- Use **Dev/Test subscriptions** or B-series VMs / Basic tiers for non-production.
- Set up **budget alerts** at 80% and 100% of monthly spend.
- Delete unused resources: stopped VMs still incur storage costs, idle App Service Plans cost money even with no apps.
- Use **Azure Advisor** recommendations — it surfaces cost, performance, and security improvements.

---

## Infrastructure as Code

- All Azure resources must be provisioned via IaC: **Bicep** (preferred) or **Terraform**.
- Never provision resources manually in the portal for anything beyond quick experiments.
- Store IaC in source control alongside the application code.
- Use parameter files per environment (`main.bicep` + `prod.parameters.json`).
- Run `what-if` / `terraform plan` before every deployment to production.
- Use Azure Verified Modules (AVM) for Bicep as the starting point for common resource types.

---

## What to Never Do

- Never store credentials, connection strings, or secrets outside of Key Vault.
- Never assign `Owner` or `Contributor` at subscription level to an application identity.
- Never expose SQL Server, Redis, or internal services directly to the internet.
- Never provision resources manually in production without corresponding IaC committed.
- Never use a single resource group for all environments.
- Never disable TDE or soft-delete on production databases or Key Vaults.
- Never ignore Azure Defender / Defender for Cloud alerts in production.
