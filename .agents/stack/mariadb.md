# MariaDB Guidelines
> Sources: MariaDB Knowledge Base, MariaDB Performance Tuning, MySQL 8.0 Reference (compatible syntax)
> Database: MariaDB 11.x · MySQL 8.0 · InnoDB · Aria · Galera Cluster

---

## Schema Design

- Always define a primary key on every table. Prefer `INT UNSIGNED AUTO_INCREMENT` or `BIGINT UNSIGNED AUTO_INCREMENT`.
- Use `UUID` for public-facing IDs (prevent enumeration). Store as `BINARY(16)` with `UUID_TO_BIN()`/`BIN_TO_UUID()` for better performance — or use `UUID_SHORT()` for time-ordered UUIDs.
- Use `NOT NULL` by default. Nullable columns require explicit justification.
- Use `FOREIGN KEY` constraints — MariaDB enforces them (InnoDB). Do not rely solely on application-level RI.
- Use `CHECK` constraints (supported since MariaDB 10.2.1) for domain validation.
- Use `UNIQUE` constraints instead of application-level uniqueness checks.
- Name tables and columns in `snake_case` consistently. Use backticks only when identifiers contain reserved words — avoid reserved words.
- Use `DATETIME` for date+time. Use `TIMESTAMP` only when timezone conversion to UTC is needed — note `TIMESTAMP` range ends at `2038-01-19` (Y2038 problem). Prefer `DATETIME` for future dates.
- Use `DECIMAL(precision, scale)` for monetary amounts — never use `FLOAT` or `DOUBLE`.
- Use `TEXT` or `VARCHAR(n)` based on data size. MariaDB allows `VARCHAR` up to 21845 bytes per row depending on row format and charset.
- Use `ROW_FORMAT=DYNAMIC` (default in 10.2+ with `innodb_default_row_format`).
- Use `CHARACTER SET utf8mb4` for full Unicode support — not `utf8` (which in MySQL/MariaDB is only 3-byte UTF-8).
- Use storage engines intentionally: InnoDB for transactional OLTP, Aria for read-heavy/caching, MEMORY for session-scoped data only.
- Use `AUTO_INCREMENT` columns with `UNSIGNED` to double the range.

---

## Indexing

- Index every foreign key column — MariaDB does not auto-index FK columns.
- Index columns used in `WHERE`, `JOIN ON`, `ORDER BY`, `GROUP BY`.
- Use **B-tree** indexes (default). Use **FULLTEXT** (with MyISAM or InnoDB) for text search. Use **SPATIAL** for geometry (`MyISAM` only).
- Use **composite (compound) indexes**: leading column must match the query's `WHERE` filter.
- Use **prefix indexes** for long `TEXT`/`VARCHAR` columns to save space:

```sql
CREATE INDEX idx_description ON articles (description(100));
```

- Use **functional indexes** (since MariaDB 10.3.3) for expressions:

```sql
CREATE INDEX idx_year_created ON [Order] ((YEAR(CreatedDate)));
```

- Use `EXPLAIN` to check index usage. Focus on `type`, `rows`, and `Extra` columns.
- Use **covering indexes** to avoid table heap lookups (when all selected columns are in the index).
- Do not over-index write-heavy tables — each index slows `INSERT`, `UPDATE`, `DELETE`.
- Use `ANALYZE TABLE` to update index cardinality stats after large data changes.
- Use `OPTIMIZE TABLE` to rebuild fragmented indexes and reclaim space — run during low-traffic windows.
- Monitor index usage with `SHOW INDEX FROM table_name` and `SHOW TABLE STATUS`.

---

## Query Writing (MariaDB / MySQL)

- Never use `SELECT *`. Explicitly name columns.
- Use `EXISTS` instead of `IN` for large subquery sets — MariaDB may optimize better.
- Use `STRAIGHT_JOIN` when you need to force join order (rare — only when the optimizer chooses poorly).
- Write sargable `WHERE` filters:

```sql
-- Bad
WHERE YEAR(OrderDate) = 2024
-- Good
WHERE OrderDate >= '2024-01-01' AND OrderDate < '2025-01-01'
```

- Use `LIMIT` / `OFFSET` for pagination on small datasets. For large datasets, prefer keyset pagination:

```sql
-- Keyset pagination (efficient)
SELECT OrderId, OrderDate
FROM [Order]
WHERE OrderId > @lastSeenId
ORDER BY OrderId
LIMIT 20;
```

- Use `INSERT ... ON DUPLICATE KEY UPDATE` for upsert operations.
- Use `REPLACE INTO` carefully — it does a `DELETE`+`INSERT`, which resets auto-increment and fires triggers differently.
- Use `INSERT IGNORE` to skip duplicates silently.
- Use `LAST_INSERT_ID()` to retrieve the last auto-increment value.
- Use `GROUP_CONCAT()` for string aggregation — mind `group_concat_max_len` setting (default 1024).
- Use `SELECT ... FOR UPDATE` for row-level locking — only within a transaction.
- Use `EXPLAIN EXTENDED` (or `EXPLAIN FORMAT=JSON`) for detailed query plan analysis.
- Use `SHOW WARNINGS` after problematic queries to see errors or warnings.

---

## Transactions & Concurrency

- Keep transactions short. Never include network I/O or external API calls inside a transaction.
- Default isolation `REPEATABLE READ` is standard InnoDB default. Switch to `READ COMMITTED` for high-concurrency workloads to reduce gap locking:

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

- Use `SET autocommit = 0` for manual transaction control — or use `START TRANSACTION`.
- Use `ROLLBACK` on error — never leave a transaction open.
- Use `SAVEPOINT` for partial rollback within a transaction.
- Be aware of InnoDB gap locks under `REPEATABLE READ` — can cause phantom-row locking and deadlocks.

---

## Stored Procedures / Functions (SQL/PSM)

- Use `LANGUAGE SQL` for simple procedures. Use `NOT DETERMINISTIC` / `DETERMINISTIC` and `CONTAINS SQL` / `NO SQL` / `READS SQL DATA` / `MODIFIES SQL DATA` correctly.
- Use parameters with `IN`, `OUT`, `INOUT` modifiers.
- Avoid row-by-row cursors — prefer set-based operations.
- Use `DECLARE ... HANDLER` for error handling:

```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
    ROLLBACK;
    RESIGNAL;
END;
```

- Use `SIGNAL` and `RESIGNAL` to raise and re-raise custom errors.
- Avoid scalar UDFs in `WHERE` clauses — they disable index usage.
- Use `SET @variable` sparingly in production code; prefer explicit procedure parameters.

---

## Performance & Tuning

- Read query plans with `EXPLAIN EXTENDED` or `EXPLAIN FORMAT=JSON`.
- Tune **InnoDB buffer pool size** (`innodb_buffer_pool_size`): typically 60-70% of RAM on dedicated DB servers.
- Tune **InnoDB log file size** (`innodb_log_file_size`): large enough to handle peak write activity during maintenance windows.
- Tune `max_connections`: not higher than what the server can support — each connection consumes memory.
- Tune `tmp_table_size` and `max_heap_table_size` to reduce disk-based temp tables.
- Tune `sort_buffer_size` per session — be careful as it's allocated per connection.
- Use **Query Cache** only if you have read-heavy workloads with infrequent writes (MariaDB still supports it; consider carefully as it can be a contention point). In MariaDB 10.1+, the query cache is present but default OFF — better to use application-level caching.
- Use `SHOW FULL PROCESSLIST` to identify long-running or blocked queries.
- Use `SHOW ENGINE INNODB STATUS` to diagnose deadlocks, lock waits, and buffer pool usage.
- Use `SHOW PROFILES` and `SHOW PROFILE` for per-query execution breakdown.
- Use `SLOW_QUERY_LOG` to identify queries exceeding `long_query_time`.
- Use **Aria** for caching-heavy read-only tables (log tables, session caches) — Aria resolves some InnoDB contention points for these workloads.
- Use **Galera Cluster** for multi-master synchronous replication — be aware of certification-based replication and flow control.

---

## Security

- Application DB user must have only required privileges (SELECT, INSERT, UPDATE, DELETE) on specific tables — never `root` or `SUPER`.
- Use `CREATE USER ... IDENTIFIED BY ...` with strong passwords. Use `ALTER USER ... PASSWORD EXPIRE` for temporary accounts.
- Use `GRANT ... ON database.table TO user@host` — be specific with host.
- Use `REVOKE` when reducing privileges — test with `SHOW GRANTS FOR user@host`.
- Use parameterized queries (prepared statements) — never concatenate user input.
- Enable TLS/SSL for client connections: `REQUIRE SSL` in `GRANT` statement.
- Use `mysql_secure_installation` to remove remote root access, anonymous accounts, and test databases.
- Consider `MAX_*_PER_HOUR` resource limits for shared / multi-tenant databases.
- Use audit logging (MariaDB Audit Plugin) for DDL and privilege changes.
- Store connection strings in environment secrets or vault — never in source code.

---

## Migration (Schema Changes)

- All schema changes go through versioned migration files — never run `ALTER TABLE` directly on production.
- Use `ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE` for online DDL where supported:

```sql
ALTER TABLE [Order] ADD COLUMN Status VARCHAR(20) DEFAULT 'Pending',
    ALGORITHM=INPLACE, LOCK=NONE;
```

- For Galera Cluster, use `SET SESSION wsrep_OSU_method = 'TOI'` (Total Order Isolation) for DDL — or use rolling schema upgrade (RSUS) for very large tables.
- Never drop a column in the same deployment as the code change that stops using it — multi-phase rollout.
- Use `pt-online-schema-change` (Percona Toolkit) or `gh-ost` for large tables where InnoDB native DDL is too slow or blocking.
- Run `ANALYZE TABLE` after large data loads to update statistics.
- Run `OPTIMIZE TABLE` during low-traffic windows for tables with heavy `DELETE`/`UPDATE` activity.

---

## What to Never Do

- Never `SELECT *` in production code.
- Never concatenate user input into SQL — always use prepared statements.
- Never use `root` or `SUPER` for application connections.
- Never place application logic or network I/O inside a database transaction.
- Never drop a column in the same deployment as the code change that stops using it.
- Never disable `innodb_doublewrite` on production — checksums alone are not sufficient for crash safety.
- Never use `REPLACE INTO` without understanding it does `DELETE`+`INSERT` (not `UPDATE`).
- Never set `innodb_buffer_pool_size` above 80% of RAM — risk of swapping.
- Never use `utf8` charset — always use `utf8mb4` for full Unicode.
- Never run migrations directly on production without testing on staging first.
- Never assume MySQL 8.0 SQL syntax is identical to MariaDB — test each dialect.
- Never use `OPTIMIZE TABLE` during peak traffic on InnoDB tables — it blocks operations.
