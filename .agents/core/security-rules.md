# Security Rules
> Sources: OWASP Top 10:2021, OWASP API Security Top 10:2023, Microsoft SDL
> Format: absolute rules — never suggestions. Violations are blockers.

---

## A01 — Broken Access Control

- Every endpoint must verify the caller is authorized to access the specific resource, not just authenticated.
- Always validate object ownership: `WHERE id = @id AND userId = @currentUserId`. Never trust IDs from the request alone.
- Enforce authorization server-side only. Never rely on hiding endpoints or UI elements as access control.
- Apply deny-by-default: return 403 unless access is explicitly granted.
- Admin and privileged endpoints must be explicitly protected — never assume a route is safe because it's "obscure".
- Never allow function-level access escalation: non-admins must not be able to call admin actions by guessing URLs.

---

## A02 — Cryptographic Failures

- Never store passwords in plaintext or with reversible encryption. Use bcrypt, Argon2, or PBKDF2.
- Never use MD5 or SHA-1 for passwords or security-sensitive hashing. Use SHA-256+ or a modern KDF.
- Never hard-code secrets, keys, or credentials in source code.
- Store secrets in Azure Key Vault, environment variables, or secrets managers — never in `appsettings.json` or `.env` committed to source.
- Always transmit sensitive data over TLS. Never HTTP for any authenticated or sensitive route.
- Never log passwords, tokens, session IDs, credit card numbers, or PII.
- Use HTTPS-only cookies: `Secure`, `HttpOnly`, `SameSite=Strict` (or `Lax` for cross-origin flows).

---

## A03 — Injection

- Never concatenate user input into SQL queries. Always use parameterized queries or EF Core ORM.
- Never concatenate user input into shell commands. Avoid running system commands with user data.
- Never concatenate user input into HTML output without encoding. Use the framework's encoding (`@Html.Encode`, Vue template binding by default encodes, etc.).
- For LDAP, XML, XPath, and NoSQL — apply the same parameterized/escape rules as SQL.
- In EF Core, use `FromSqlInterpolated` (not `FromSqlRaw` with string concat) when raw SQL is unavoidable.

---

## A04 — Insecure Design

- Design threat models before implementing security-sensitive features (auth, payments, file uploads).
- Never design flows where a user can escalate privileges simply by changing a request parameter.
- Limit business flow automation: rate limit and add CAPTCHA/challenge on flows vulnerable to automated abuse (account creation, checkout, OTP).
- Do not trust client-supplied values for price, discount, roles, or permissions.

---

## A05 — Security Misconfiguration

- Disable all debug/diagnostic endpoints in production. Remove swagger/redoc from non-dev environments unless access-controlled.
- Never run apps with development exception pages (`UseDeveloperExceptionPage`) in production.
- Remove default credentials from all infrastructure (DB servers, admin consoles, Redis, etc.).
- Apply least-privilege to all service accounts and DB connection strings.
- Disable unused features, services, ports, and HTTP methods.
- Set security response headers: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`.
- Never expose stack traces, internal error messages, or framework versions to clients.

---

## A06 — Vulnerable and Outdated Components

- Keep all NuGet, npm, and pip packages up to date. Run dependency audits in CI.
- Never use packages with known critical CVEs. Use `dotnet list package --vulnerable`, `npm audit`, `pip-audit`.
- Pin dependency versions in production builds. Do not use `*` or `latest`.
- Remove unused dependencies. Every package is an attack surface.

---

## A07 — Identification and Authentication Failures

- Never implement custom authentication. Use ASP.NET Core Identity, Azure AD, or a proven identity provider.
- Enforce multi-factor authentication on all admin and high-privilege accounts.
- Never allow brute force: implement account lockout and rate limiting on auth endpoints.
- Token expiry: access tokens short-lived (15 min), refresh tokens rotatable and revocable.
- Never expose session tokens or JWTs in URLs. Transmit in `Authorization` header or `HttpOnly` cookie.
- Invalidate sessions on logout and password change server-side.
- Generate random, unpredictable session IDs (UUID v4 minimum). Never sequential.

---

## A08 — Software and Data Integrity Failures

- Never deserialize untrusted data with `BinaryFormatter` or polymorphic JSON without type discrimination.
- Verify integrity of third-party libraries in CI (checksums, Sigstore, package lock files).
- Validate all CI/CD pipeline inputs. Do not allow arbitrary script injection via PR comments or issue titles.
- Use content security policy to prevent unauthorized script execution in the browser.

---

## A09 — Security Logging and Monitoring Failures

- Log all authentication events (success and failure), authorization failures, and significant business events.
- Log with context: timestamp (UTC), user ID, IP, endpoint, action — never the secret or credential itself.
- Alert on repeated auth failures, unusual access patterns, and privilege escalation attempts.
- Log to a tamper-resistant, centralized system — not the local file system of the app server.
- Retain security logs for at minimum 90 days.

---

## A10 — Server-Side Request Forgery (SSRF)

- Never fetch a URL supplied directly by the user without validation.
- Validate and allowlist target URLs or domains before making outbound HTTP requests.
- Block requests to private/internal IP ranges (169.254.x.x, 10.x, 172.16–31.x, 192.168.x.x, localhost) from user-controlled URLs.
- Use `HttpClientFactory` with explicit base addresses — never dynamic URL construction from user input.

---

## API Security (OWASP API Top 10:2023)

- BOLA (Broken Object Level Authorization): Every API response must be scoped to the authenticated user. Never return all records and filter client-side.
- Never expose more data in API responses than the caller needs. Use DTOs/projections — never return full entity objects with internal fields.
- Rate limit all public and authenticated API endpoints. Apply to both per-user and global limits.
- Validate all API inputs: data type, length, format, range. Reject at the controller/endpoint boundary.
- Do not expose internal IDs in sequential integer form. Use UUIDs or opaque tokens.
- Never allow mass assignment: explicitly define which fields are bindable. Use `[Bind]` or dedicated DTO classes — never bind directly to domain entities.

---

## Input Validation

- Validate all input at trust boundaries (API endpoint entry points). Never assume internal calls are safe.
- Validate type, length, format, and range. Reject early with a clear error.
- Use allowlist validation (define what is acceptable) not denylist (block known bad).
- Sanitize file upload names: strip directory traversal (`../`), enforce extension allowlists, store outside web root.
- Limit upload file size at the server level, not just client-side.

---

## Secrets Management

- Rotate secrets on a schedule or immediately on suspected exposure.
- Never commit `.env`, `appsettings.*.json`, or any file with real credentials to source control.
- Use Azure Managed Identity to access Azure resources — eliminates secret management for in-platform services.
- Add secret file patterns to `.gitignore` and pre-commit hooks.

---

## What to Never Do

- Never concatenate user input into SQL, HTML, shell commands, or URLs.
- Never store passwords in plaintext or reversible format.
- Never hard-code credentials or secrets.
- Never expose stack traces to external clients.
- Never rely on security through obscurity (hidden endpoints, unlinked pages).
- Never trust the client for authorization decisions (roles, prices, IDs, flags).
- Never run debug/dev configurations in production.
- Never serialize/deserialize untrusted data with unsafe deserializers.
