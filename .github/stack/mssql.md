# SQL Server Guidelines
> Sources: Microsoft SQL Server Best Practices, Azure SQL Performance Guidance
> Database: SQL Server 2022+ · Azure SQL Database · T-SQL

---

## Schema Design

- Always define a primary key on every table. Prefer `INT IDENTITY(1,1)` or `BIGINT IDENTITY(1,1)` for surrogate keys.
- Use `UNIQUEIDENTIFIER` with `NEWSEQUENTIALID()` for public-facing IDs — avoids fragmentation compared to `NEWID()`.
- Use `NOT NULL` by default. Nullable columns require justification.
- Every table must have `FOREIGN KEY` constraints — never rely solely on application-level referential integrity.
- Use `CHECK` constraints for domain validation (status enums, positive amounts, date ranges).
- Use `UNIQUE` constraints instead of application-level uniqueness checks.
- Name tables as singular nouns: `[Order]`, `[Customer]`, `[Product]`.
- Name columns in `PascalCase` consistently. Use `[brackets]` only when names contain reserved words — better to avoid reserved words entirely.
- Prefer `DATETIME2` over `DATETIME` (more precision, larger range, smaller storage).
- Use `NVARCHAR(n)` over `VARCHAR(n)` if there is any chance of Unicode data. Use `NVARCHAR(MAX)` only when data exceeds 4000 characters.
- Use `ROWVERSION` (timestamp) for optimistic concurrency control.

---

## Indexing

- Index every foreign key column — the engine does not do this automatically.
- Index columns used in `WHERE`, `JOIN ON`, `ORDER BY`, `GROUP BY` frequently.
- Composite indexes: order columns from most selective (highest cardinality) to least.
- Use **covering indexes** with `INCLUDE` to avoid key lookups on read-heavy queries:

```sql
CREATE NONCLUSTERED INDEX IX_Orders_CustomerId
ON [Order] (CustomerId)
INCLUDE (OrderDate, TotalAmount, Status);
```

- Use **filtered indexes** for sparse conditions:

```sql
CREATE NONCLUSTERED INDEX IX_Orders_Active
ON [Order] (CreatedDate)
WHERE IsActive = 1;
```

- Use **columnstore indexes** for data warehousing / analytical workloads — do not use on OLTP tables with frequent point updates.
- Do not over-index write-heavy tables — each index slows `INSERT`, `UPDATE`, `DELETE`.
- Monitor and remove unused indexes via `sys.dm_db_index_usage_stats`.
- Rebuild (`ALTER INDEX ... REBUILD`) or reorganize (`REORGANIZE`) fragmented indexes regularly (threshold: >30% rebuild, 5-30% reorganize).
- Keep the clustered index narrow and ever-increasing (e.g., `INT IDENTITY`). Avoid GUIDs as clustered keys — they cause fragmentation.

---

## Query Writing (T-SQL)

- Never use `SELECT *`. Explicitly name columns.
- Always use schema prefix: `FROM dbo.[Order]` not `FROM [Order]`.
- Use `EXISTS` instead of `IN` for existence checks — better performance with subqueries.
- Use `WHERE` filters that are sargable — avoid wrapping indexed columns in functions:

```sql
-- Bad
WHERE YEAR(OrderDate) = 2024
-- Good
WHERE OrderDate >= '2024-01-01' AND OrderDate < '2025-01-01'
```

- Use `TOP` with `ORDER BY` for pagination. Prefer keyset pagination over `OFFSET` for large datasets:

```sql
-- Keyset pagination (efficient)
SELECT TOP 20 OrderId, OrderDate
FROM [Order]
WHERE OrderId > @lastSeenId
ORDER BY OrderId;

-- Avoid OFFSET for deep pages
```

- Use `WITH (NOLOCK)` only for non-critical reporting where dirty reads are acceptable. Never on transactional queries.
- Prefer `MERGE` over separate `INSERT`/`UPDATE` for upsert patterns, but test carefully — `MERGE` has known edge cases.
- Use `OUTPUT` clause to return inserted/updated/deleted rows without a second query.
- Use `TRY_CAST` and `TRY_CONVERT` instead of `CAST`/`CONVERT` when conversion failure is possible.
- Use `STRING_AGG` instead of `FOR XML PATH('')` for string concatenation (SQL Server 2017+).
- Use `APPLY` (`CROSS APPLY` / `OUTER APPLY`) for correlated top-N per group queries.

```sql
SELECT o.OrderId, t.TopProduct
FROM [Order] o
CROSS APPLY (
    SELECT TOP 1 ProductName AS TopProduct
    FROM OrderItem oi
    WHERE oi.OrderId = o.OrderId
    ORDER BY oi.UnitPrice DESC
) t;
```

---

## Transactions

- Keep transactions as short as possible. Never include HTTP calls, file I/O, or external API calls inside a transaction.
- Use **RCSI (READ COMMITTED SNAPSHOT ISOLATION)** for high-concurrency OLTP workloads — enables non-blocking reads.
- Enable at database level: `ALTER DATABASE MyDb SET READ_COMMITTED_SNAPSHOT ON;`
- Use `SERIALIZABLE` only when absolute consistency is required — understand the blocking tradeoff.
- Always use `BEGIN TRY ... BEGIN CATCH ... ROLLBACK` pattern. Never leave a transaction open on error.
- Use `SET XACT_ABORT ON` at the top of stored procedures to auto-rollback on all runtime errors.
- Avoid distributed transactions. Design data ownership to minimize cross-database operations.

---

## Stored Procedures

- Use `SET NOCOUNT ON` at the start of every stored procedure to suppress DONE_IN_PROC messages.
- Use `SET XACT_ABORT ON` for automatic rollback on errors.
- Always use parameters — never concatenate input into dynamic SQL. Use `sp_executesql` with parameters if dynamic SQL is unavoidable.
- Name conventions: `usp_{Entity}_{Action}` (e.g., `usp_Order_GetById`).
- Use `WITH RECOMPILE` only for queries with highly variable parameters (rare).
- Prefer table-valued parameters (TVPs) over comma-separated strings for passing lists.
- Avoid scalar UDFs in `WHERE` clauses or on large rowsets — they disable parallelism.

---

## Security

- Application DB user must have only required permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE` on specific tables) — never `db_owner` or `sysadmin`.
- Never use `sa` for application connections.
- Use Azure Managed Identity or integrated security (Windows Auth) over SQL authentication where possible.
- Always parameterize queries — never concatenate user input.
- Use **Always Encrypted** for sensitive columns (PII, financial data) with secure enclaves.
- Enable **Transparent Data Encryption (TDE)** on all databases.
- Use **SQL Server Audit** or built-in auditing for privileged access tracking.
- Store connection strings in Azure Key Vault or environment secrets — never in source code.

---

## Performance

- Read execution plans before optimizing. Use `SET STATISTICS IO ON` and `SET STATISTICS TIME ON`.
- Use **Query Store** to identify regressed queries: `ALTER DATABASE MyDb SET QUERY_STORE = ON;`.
- Update statistics after large data loads: `UPDATE STATISTICS [TableName];` with `FULLSCAN` for accuracy.
- Use `sys.dm_exec_query_stats` and `sys.dm_exec_sql_text` to find high-CPU or high-I/O queries.
- Avoid cursors — use set-based operations. If row-by-row is unavoidable, use a `WHILE` loop with `TOP 1`.
- Use **table-valued parameters** (TVPs) instead of dynamic `IN` lists or XML for batch operations.
- Batch large writes: `UPDATE TOP (1000)` or `DELETE TOP (1000)` in a loop to avoid lock escalation.
- Use **tempdb** wisely: optimize `tempdb` file placement (multiple files), avoid excessive `#temp` table usage.

---

## Migrations (EF Core / Flyway / SQL Scripts)

- All schema changes go through versioned migration files — never run `ALTER TABLE` directly on production.
- Each migration must be small and reversible. Provide a `DOWN` script for rollback.
- Never drop a column or table in the same deployment as the code change that stops using it — use a multi-phase rollout:
  1. Phase 1: Deploy code that stops reading/writing the column.
  2. Phase 2 (next deployment): Drop the column.
- Test migrations against production-sized data in staging before deploying.
- Use `ONLINE = ON` for index operations on large tables (Enterprise edition).

---

## What to Never Do

- Never `SELECT *` in production code.
- Never concatenate user input into SQL — always parameterize.
- Never use `sa` or `db_owner` for application connections.
- Never place HTTP calls, file I/O, or external API calls inside a database transaction.
- Never drop a column or table in the same deployment as the code change that stops using it.
- Never use `NOLOCK` on transactional (write) queries.
- Never use cursors when a set-based solution exists.
- Never rely on application-level uniqueness instead of `UNIQUE` constraints.
- Never use `NEWID()` as a clustered index key — use `NEWSEQUENTIALID()` or `INT IDENTITY`.
- Never run migrations directly on production without testing on staging first.
