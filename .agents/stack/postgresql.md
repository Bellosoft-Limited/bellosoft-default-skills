# PostgreSQL Guidelines
> Sources: PostgreSQL Documentation, PostgresqlCO.NF Performance Tuning
> Database: PostgreSQL 16+ · PL/pgSQL

---

## Schema Design

- Always define a primary key on every table. Prefer `BIGSERIAL` or `UUID` for surrogate keys.
- Use `UUID` (with `gen_random_uuid()`) for public-facing IDs — prevents enumeration. Keep internal keys as `BIGSERIAL` for join performance.
- Use `NOT NULL` by default. Nullable columns require explicit justification.
- Use `FOREIGN KEY` constraints — never rely on application-level referential integrity.
- Use `CHECK` constraints for domain validation.
- Use `EXCLUDE` constraints for complex uniqueness rules (e.g., time ranges that must not overlap).
- Use `UNIQUE` constraints instead of application-level uniqueness checks.
- Name tables and columns in `snake_case` consistently. Use double quotes only when absolutely necessary — better to avoid quoted identifiers entirely.
- Prefer `TEXT` over `VARCHAR(n)` — they perform identically in PostgreSQL. Use `VARCHAR(n)` only when a length limit is a business requirement.
- Use `TIMESTAMPTZ` (timestamptz) over `TIMESTAMP` — always store times in UTC, convert on display.
- Use `NUMERIC(precision, scale)` for monetary amounts — never use `FLOAT` or `REAL`.
- Use `JSONB` over `JSON` for JSON columns — `JSONB` supports indexing (`GIN`) and is more efficient.
- Use `ARRAY` type when an ordered set of same-type values is needed (e.g., tags). Use `GIN` index on array columns.
- Use `IDENTITY` columns (generated always as identity) instead of `SERIAL` for stricter SQL standard compliance:

```sql
CREATE TABLE [Order] (
    OrderId INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
);
```

---

## Indexing

- Index every foreign key column — PostgreSQL does not create indexes on FKs automatically.
- Index columns used in `WHERE`, `JOIN ON`, `ORDER BY`, `GROUP BY`.
- Use **B-tree** for most indexes (default). Use **GIN** for JSONB, array, full-text search columns. Use **GiST** for full-text search, range types, geometry.
- Use **BRIN** indexes for very large tables where rows are physically ordered (e.g., time-series data) — much smaller than B-tree.
- Composite indexes: order columns from most selective to least. Leading column must match the query's filter pattern.
- Use **partial indexes** for sparse conditions:

```sql
CREATE INDEX idx_orders_active ON [Order] (CreatedDate) WHERE IsActive = TRUE;
```

- Use **covering indexes** (INCLUDE) for index-only scans:

```sql
CREATE INDEX idx_orders_customer ON [Order] (CustomerId) INCLUDE (TotalAmount, Status);
```

- Use `CREATE INDEX CONCURRENTLY` to avoid blocking writes during index creation on production.
- Monitor unused indexes: `pg_stat_user_indexes` + `pg_stat_all_indexes`.
- Remove unused indexes: `DROP INDEX CONCURRENTLY idx_name;`.
- Reindex: `REINDEX INDEX CONCURRENTLY idx_name;` — use `CONCURRENTLY` to avoid locking.
- Consider `pg_repack` to rebuild bloated indexes and tables without locking.

---

## Query Writing (PL/pgSQL)

- Never use `SELECT *`. Explicitly name columns.
- Use `EXISTS` instead of `IN` for subquery existence checks.
- Write sargable `WHERE` filters — avoid wrapping indexed columns in functions:

```sql
-- Bad
WHERE EXTRACT(YEAR FROM created_at) = 2024
-- Good
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
```

- Use `LIMIT` / `OFFSET` for pagination on small datasets. Use **keyset pagination** for large datasets:

```sql
-- Keyset pagination (efficient for large sets)
SELECT OrderId, OrderDate
FROM [Order]
WHERE OrderId > @lastSeenId
ORDER BY OrderId
LIMIT 20;
```

- Use `LATERAL` joins for correlated top-N per group:

```sql
SELECT o.OrderId, t.TopProduct
FROM [Order] o
LEFT JOIN LATERAL (
    SELECT ProductName AS TopProduct
    FROM OrderItem oi
    WHERE oi.OrderId = o.OrderId
    ORDER BY oi.UnitPrice DESC
    LIMIT 1
) t ON true;
```

- Use `DISTINCT ON` for getting the first row per group:

```sql
SELECT DISTINCT ON (CustomerId) CustomerId, OrderId, OrderDate
FROM [Order]
ORDER BY CustomerId, OrderDate DESC;
```

- Use `ROW_NUMBER()` / `RANK()` / `DENSE_RANK()` for window-based ordering.
- Use `ON CONFLICT DO UPDATE` for upsert operations (INSERT ... ON CONFLICT).
- Use `ORDER BY NULLS LAST` or `NULLS FIRST` explicitly when sorting nullable columns.
- Use `RETURNING` clause to return data from `INSERT`, `UPDATE`, `DELETE`.

---

## Transactions & Concurrency

- Keep transactions short. Never include application logic or network I/O inside a transaction.
- Default isolation `READ COMMITTED` is suitable for most OLTP.
- Use `REPEATABLE READ` when a transaction must see a consistent snapshot across multiple queries and prevent non-repeatable reads.
- Use `SERIALIZABLE` only when you understand the performance cost and have tested for serialization failures.
- Use `SELECT ... FOR UPDATE` sparingly — avoid long-held row locks.
- Use `SKIP LOCKED` and `NOWAIT` for queue-like workloads to avoid blocking.
- Use advisory locks (`pg_advisory_lock`) for application-level coordination outside the table lock system.
- Use `SAVEPOINT` for partial rollback within a transaction.

---

## Functions and Procedures

- Use `LANGUAGE plpgsql` for procedural logic, `LANGUAGE sql` for simple set-returning functions.
- Prefer set-based operations over row-by-row processing (avoid `FOR` loops).
- Use `SECURITY INVOKER` as default. Use `SECURITY DEFINER` only when function needs elevated privileges — and set `SEARCH_PATH` explicitly.
- Use `IMMUTABLE` / `STABLE` / `VOLATILE` correctly — incorrect classification breaks index usage.
- Use `RETURNS TABLE` or `RETURNS SETOF` for set-returning functions.
- Prefer `VIEW` with `MATERIALIZED` option for expensive, infrequently-changing aggregations.

---

## Performance

- Read query plans with `EXPLAIN (ANALYZE, BUFFERS)` before tuning.
- Use `pg_stat_statements` to identify high-frequency or high-latency queries. Enable by default.
- Run `ANALYZE` after large data loads or bulk operations to update statistics.
- Tune `work_mem` for sort-heavy operations (per-operation, not per-session — be careful).
- Tune `shared_buffers`: typically 25% of RAM.
- Tune `effective_cache_size`: typically 50-75% of RAM.
- Use connection pooling (PgBouncer, built-in pool) — every connection is a forked process in PostgreSQL.
- Use `EXPLAIN (BUFFERS)` to check if queries are hitting cache or reading from disk.
- Avoid `SELECT COUNT(*)` on large tables for existence — use `EXISTS (SELECT 1 ...)` aka `EXPLAIN (ANALYZE)`.
- Use `CLUSTER` to physically reorder a table based on an index (one-time operation for time-series).
- Use `VACUUM` regularly — preferably with `autovacuum` tuned appropriately. Monitor `pg_stat_user_tables.n_dead_tup`.
- Use `VACUUM FREEZE` preventively to avoid transaction ID wraparound.

---

## Security

- Application DB user should have only required privileges (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on specific tables — never superuser.
- Use **row-level security (RLS)** for multi-tenant data isolation:

```sql
ALTER TABLE [Order] ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON [Order]
    USING (tenant_id = current_setting('app.tenant_id')::INT);
```

- Use `pgcrypto` for encrypting sensitive columns at the application level.
- Use `pgaudit` for auditing privileged access and DDL changes.
- Never concatenate user input — always use parameterized queries (`$1`, `$2`).
- Use SSL/TLS for all client connections.
- Store connection strings in environment secrets or a vault — never in source code.

---

## Migrations

- All schema changes go through versioned migration files (EF Core, Flyway, or plain SQL files).
- Never run `ALTER TABLE` directly on production without a migration.
- Use `CREATE INDEX CONCURRENTLY` for indexes on large tables to avoid locking.
- Use `ALTER TABLE ... SET NOT NULL` only after verifying no NULLs exist and adding a `CHECK` first if needed.
- Never drop a column in the same deployment as the code change that stops using it — multi-phase rollout.
- Use `SET session_replication_role = replica` to bypass triggers during data-only migrations (not for schema changes).

---

## What to Never Do

- Never `SELECT *` in production code.
- Never concatenate user input into SQL — always use parameterized queries.
- Never use `SUPERUSER` or the `postgres` superuser account for application connections.
- Never place application logic or network I/O inside a database transaction.
- Never drop a column or table in the same deployment as the code change that stops using it.
- Never disable `autovacuum` on production tables.
- Never use `FOR UPDATE` for read-only queries.
- Never rely on application-level uniqueness instead of `UNIQUE` constraints.
- Never use `CLUSTER` on a table that receives concurrent writes during the operation.
- Never use `SERIALIZABLE` isolation without testing for serialization failures.
- Never run migrations directly on production without testing on staging first.
