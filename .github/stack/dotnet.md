# .NET Stack Guidelines
> Sources: Microsoft ASP.NET Core Best Practices, EF Core Performance Docs, Microsoft Learn
> Stack: .NET 9 / .NET 10 · ASP.NET Core · Entity Framework Core · C#

---

## Async / Threading

- Never call `.Result` or `.Wait()` on a Task in ASP.NET Core. Use `await` everywhere.
- Never use `Task.Run` to make synchronous APIs async. It just moves the blocking to a thread pool thread.
- Never use `async void` except in event handlers. Always return `Task` or `Task<T>`.
- Use `CancellationToken` parameters on all public async methods and pass them through to EF and HTTP calls.
- `ConfigureAwait(false)` in library code. Not required in ASP.NET Core controller/middleware code (no sync context).
- Do not capture `HttpContext` in background threads. Copy needed values (e.g. path, user) before launching background work.
- Do not capture scoped services (`DbContext`, etc.) in background tasks. Create a new `IServiceScope` using `IServiceScopeFactory`.
- `HttpContext` is not thread-safe. Never access it from multiple threads in parallel.
- Do not use `HttpContext` after the request has completed.

---

## ASP.NET Core

### Controllers and actions
- All controller actions that do any I/O must be `async Task<IActionResult>`.
- Return `IActionResult` (or typed `ActionResult<T>`) — never `void` or raw objects.
- Use `[ApiController]` attribute on all API controllers. Enables automatic model validation and binding.
- Use `ProblemDetails` for error responses (RFC 7807). Do not return plain string errors.
- Validate input in controllers using `ModelState` or FluentValidation — never in the service layer alone.
- Never read `HttpRequest.Form` directly. Use `ReadFormAsync()`.
- Never assume `HttpRequest.ContentLength` is non-null.

### Middleware
- Keep middleware fast. Avoid long-running work in middleware executed on every request.
- Never call `next()` after writing to the response body.
- Use `OnStarting` callback to set headers before the response starts. Do not set headers after `next()`.
- Check `Response.HasStarted` before modifying headers.

### Dependency injection
- Register services with the correct lifetime: `Singleton` for stateless/shared, `Scoped` for per-request, `Transient` for lightweight short-lived.
- Never inject a `Scoped` service into a `Singleton`. Use `IServiceScopeFactory` to resolve scoped services from singletons.
- Never store `IHttpContextAccessor.HttpContext` in a field. Access `HttpContext` on each use, check for null.

### HTTP clients
- Never create and dispose `HttpClient` directly. Always use `IHttpClientFactory`.
- Register named or typed HTTP clients in `Program.cs` via `AddHttpClient`.

### Response and request body
- Use `System.Text.Json` (built-in) — not `Newtonsoft.Json` unless the project explicitly requires it.
- Never read the entire request body into memory for large payloads. Stream it.
- Avoid reading request/response bodies synchronously (Kestrel does not support sync reads).

### Performance
- Paginate all list endpoints. Never return unbounded collections.
- Return `IAsyncEnumerable<T>` for streaming large results from endpoints instead of materializing to a list first.
- Do not allocate large objects (>= 85 KB) on hot paths. Use `ArrayPool<T>` for large buffers.
- Cache aggressively. Use `IMemoryCache` for in-process, `IDistributedCache` for multi-instance.
- Enable response compression via `UseResponseCompression()` middleware.
- Avoid throwing exceptions for control flow in hot paths.
- Use in-process IIS hosting (default in .NET 3+).

---

## Entity Framework Core

### Querying
- Use `.AsNoTracking()` for all read-only queries. It is ~30% faster and uses less memory.
- Use `.AsNoTrackingWithIdentityResolution()` when no-tracking but need de-duplicated entities.
- Project only what you need with `.Select(...)`. Never load full entities when only a few columns are needed.
- Always paginate. Use `.Skip()` / `.Take()` or keyset pagination for large datasets.
- Avoid `N+1` queries. Use `.Include()` for eager loading, or explicit projection.
- Never use lazy loading in web applications. Enable it only with deliberate intent and awareness of N+1 risk.
- Use `.AsSplitQuery()` when loading multiple collection navigations to avoid cartesian explosion.
- Use `AsAsyncEnumerable()` for streaming large result sets instead of `ToListAsync()`.
- Never use `FromSqlRaw` with unsanitized user input. Use `FromSqlInterpolated` or parameterized form.

### Writes
- Use `SaveChangesAsync()`, never `SaveChanges()`.
- Use `ExecuteUpdateAsync()` and `ExecuteDeleteAsync()` (EF 7+) for bulk updates/deletes instead of loading entities.
- Do not reuse `DbContext` across requests. It is scoped by default in ASP.NET Core — keep it that way.
- Use `DbContext` pooling (`AddDbContextPool`) for high-throughput APIs.

### Schema and modeling
- Always define explicit primary keys. Never rely on conventions alone for key type or naming.
- Index foreign keys. EF does not do this automatically.
- Use `HasConversion` or value objects for domain value types — do not store enums as magic strings.
- Use migrations. Never `EnsureCreated()` in production.
- Use `IsRequired()` to enforce `NOT NULL` — do not rely on nullable reference type inference alone.

---

## Minimal APIs (preferred for .NET 9/10 APIs)

- Prefer Minimal APIs over MVC controllers for new APIs. Use controllers only when you need filters, conventions, or complex routing.
- Group related endpoints with `RouteGroupBuilder` (`app.MapGroup`).
- Use typed results (`TypedResults.Ok(...)`) over `Results.Ok(...)` for compile-time correctness.
- Validate input using FluentValidation or endpoint filters — never assume input is safe.
- Use `[FromServices]` for DI in Minimal API handlers.

---

## .NET AI and MCP (.NET AI Extensions)

- Use `Microsoft.Extensions.AI` abstractions — never depend on a concrete provider SDK directly.
- Register AI services via DI (`builder.Services.AddChatClient(...)`) — treat AI like any other service.
- Use structured outputs (typed deserialization) rather than raw string parsing of LLM responses.
- Apply `CancellationToken` on all AI completion calls.
- Log prompts and completions at `Debug` level for observability. Never log at `Information` in production (token cost + PII risk).
- For MCP servers in .NET: use `Microsoft.Extensions.AI.Mcp` — follow the same DI and cancellation patterns as HTTP clients.

---

## Logging and Observability

- Use `ILogger<T>` via DI — never static loggers or `Console.WriteLine`.
- Use structured logging with named parameters: `_logger.LogInformation("Order {OrderId} created", id)` — not string interpolation.
- Use `LoggerMessage.Define` for high-frequency log messages on hot paths (avoids boxing allocations).
- Log at the correct level: `Trace`/`Debug` for diagnostics, `Information` for significant business events, `Warning` for recoverable issues, `Error` for failures, `Critical` for fatal.
- Never log sensitive data: passwords, tokens, PII, connection strings.
- Add Application Insights or OpenTelemetry in production for distributed tracing.

---

## Configuration and Secrets

- Use `IOptions<T>` pattern for typed configuration. Never use `IConfiguration` directly in application services.
- Validate configuration on startup with `ValidateDataAnnotations()` and `ValidateOnStart()`.
- Never store secrets in `appsettings.json`. Use `dotnet user-secrets` locally and Azure Key Vault in production.
- Use environment-specific config: `appsettings.Production.json` for production overrides.

---

## What to Never Do

- Never `.Result` or `.Wait()` a Task in ASP.NET Core.
- Never `new HttpClient()` — always use `IHttpClientFactory`.
- Never use lazy loading in production web APIs.
- Never `SELECT *` via raw SQL or over-project via EF (load full entities when a projection suffices).
- Never store secrets in source code or `appsettings.json`.
- Never use `EnsureCreated()` in production — use migrations.
- Never swallow exceptions in middleware (`catch` with empty body).
- Never access `HttpContext` from a background thread without copying values first.
