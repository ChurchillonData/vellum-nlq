# Safety Model

This document is the complete story of how Vellum-NLQ prevents unsafe queries from reaching the database. If you are a hiring reviewer evaluating the safety claims in the README, this is the document to read.

The system has three independent safety layers. The SQL guard is the first. The database role is the second. The audit log is the third. Each layer is sufficient on its own to prevent the most common failure mode. Together they provide defence in depth.

If any layer fails, the next layer catches the failure. If all three fail, the failure is recorded and the application surfaces it loudly. Silent failure is the only outcome this system is designed to make impossible.

## What this system protects against

Before describing the controls, this is what they protect against, in rough order of likelihood.

1. **LLM hallucination of unsafe SQL.** The intent interpreter or the generator produces SQL that is structurally valid but references tables or columns that should not be exposed.

2. **Prompt injection through user questions.** A user question contains text designed to manipulate the model into generating destructive SQL or exfiltrating data through a creative query path.

3. **Catalogue misconfiguration.** A metric definition references a table that contains sensitive data the catalogue owner did not intend to expose.

4. **Library bugs.** SQLGlot or SQLAlchemy emits SQL that does not match what the generator intended, or fails to parse SQL it should have rejected.

5. **Operational mistakes.** A developer running the application with the wrong database credentials, a misconfigured Docker Compose file, a typo in an environment variable.

6. **Compromised LLM provider.** A future model release behaves differently in ways that bypass the existing prompt structure.

For each of these, the safety controls below provide either prevention or detection, and usually both.

## Layer 1: The SQL Guard

The SQL Guard receives the generated SQL string and parses it into a SQLGlot AST before any database connection is touched. It walks the tree and applies eleven checks in strict order. A failure at any check stops the request and returns a structured `ValidationError`. The SQL string never reaches the database.

The checks are ordered so that the cheapest ones run first and the most expensive ones run last. If you are reading this code in `backend/app/sql/guard.py`, the order in this document matches the order in the file.

### Check 1: Statement type

The root node of the parsed AST must be a `SELECT`. The guard rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `CREATE`, `MERGE`, `CALL`, `COPY`, `VACUUM`, `ANALYZE`, `EXPLAIN`, `SHOW`, and `SET`.

`EXPLAIN` is rejected because it can be used to leak schema information without producing rows. The application has no need for it at runtime.

### Check 2: Single statement

SQLGlot returns a list of parsed statements. The guard requires exactly one. Two or more statements separated by semicolons indicates either a generator bug or an injection attempt. Either way, reject.

### Check 3: Table allowlist

Every table reference in the `FROM` clause, every `JOIN`, every subquery, and every CTE must appear in `catalogues/health-uk/tables.yaml`. The guard walks the AST and collects every `Table` node, then checks each name against the allowlist.

This is the check that prevents the model from inventing tables. If the model generates `SELECT * FROM pg_authid` the guard rejects it at this check because `pg_authid` is not in the allowlist.

### Check 4: Column allowlist

Every column reference must appear in the columns list of its table in `tables.yaml`. Wildcards (`SELECT *`) are rejected because they expand to the full column set and bypass column-level control. The generator never emits wildcards. If one appears, something has gone wrong.

The check is column-by-table, not column-by-name. A column named `id` in the `claims` table is on the allowlist. A column named `id` in `pg_authid` is not on the allowlist, even though the column name matches.

### Check 5: Function allowlist

The allowed functions are listed in `backend/app/sql/allowlist.py`. The current set is:

- Aggregates: `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, `PERCENTILE_CONT`
- Math: `ROUND`, `ABS`, `CEIL`, `FLOOR`
- Null handling: `COALESCE`, `NULLIF`
- Date functions: `DATE_TRUNC`, `EXTRACT`, `AGE`, `NOW`, `CURRENT_DATE`
- Conditionals: `CASE`, `GREATEST`, `LEAST`
- Casts: `CAST`

Anything else is rejected. This blocks `pg_read_file`, `pg_ls_dir`, `dblink_exec`, `lo_import`, and the long tail of Postgres functions that can read files, execute shell commands, or perform network calls.

When a legitimate use case requires a new function, the function is added to the allowlist in a separate pull request with its own justification and tests. The default answer is no.

### Check 6: Join graph

Every join condition must match an edge in `catalogues/health-uk/joins.yaml`. The guard extracts the join predicates from the AST, normalises them, and checks each one against the declared graph.

Cross joins (`FROM a, b`) are rejected. Lateral joins are rejected. Self-joins are rejected unless explicitly declared in the graph, which they are not in the current catalogue.

This check is what prevents the model from inventing join paths that produce technically valid but semantically wrong results.

### Check 7: Subquery containment

Subqueries are allowed in `WHERE` clauses for predicate logic (`WHERE x IN (SELECT ...)`) and in `FROM` clauses when wrapped in a CTE. Every subquery is validated recursively against the same allowlists. CTEs are parsed and walked the same way.

Correlated subqueries are allowed but the correlation must reference an allowlisted column in the outer query.

### Check 8: LIMIT enforcement

If the statement has no `LIMIT`, the guard injects `LIMIT 10000`. If the statement has a `LIMIT` above the cap, the guard rewrites it down to the cap.

The cap is in `backend/app/config.py` as `MAX_RESULT_ROWS`. It is set to ten thousand. Most legitimate analytics questions return under a hundred rows. The cap exists to prevent a malformed query from returning the entire claims table.

### Check 9: Schema isolation

References to `information_schema`, `pg_catalog`, `pg_toast`, and any schema name other than the application schema are rejected. This prevents schema enumeration attacks where the model is tricked into listing the database's tables and columns.

### Check 10: Comment stripping

SQL comments (`-- ...` and `/* ... */`) are stripped before parsing. The generator has no reason to emit comments. Comments in generated SQL indicate either a generator bug or an attempt to hide content from the parser.

### Check 11: Parameter binding

Every literal in the generated SQL must be a bound parameter, not an inlined value. The generator uses SQLAlchemy Core to construct queries, which produces parameterised SQL by default. The guard confirms that the AST contains parameter placeholders, not literal values, in `WHERE` predicates.

A literal in the `WHERE` clause is not necessarily an injection, but it is a sign that the generator was bypassed. The guard rejects to be safe.

## Layer 2: The database role

The application connects to Postgres using a role configured with:

```sql
CREATE ROLE vellum_reader LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA public TO vellum_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vellum_reader;
ALTER ROLE vellum_reader SET statement_timeout = '15s';
ALTER ROLE vellum_reader SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE vellum_reader SET work_mem = '32MB';
ALTER ROLE vellum_reader SET search_path = 'public';
```

The role has no `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, or DDL privileges. It cannot read system catalogues (`pg_catalog` permissions are revoked at the database level).

If the SQL Guard were entirely bypassed and a destructive statement reached the database, the database would reject it with a permissions error. The application logs the error and returns a 500 response. The destructive statement does not execute.

Migrations and seeding use separate roles (`vellum_migrator` and `vellum_seeder`) configured in `docker-compose.yml`. The application never has access to those credentials.

## Layer 3: The audit log

Every request, regardless of outcome, writes a row to the `audit_log` table before the response is returned. The audit log is in a separate schema (`audit.audit_log`) that the read-only role cannot read.

The audit row contains:

- The full natural-language question
- The structured intent extracted by the interpreter
- The generated SQL string (whether or not it executed)
- The validation outcome with the specific rule that fired, if any
- The number of rows returned, if executed
- The latency in milliseconds
- A UUID query ID returned to the client

The audit log uses an append-only schema with no `UPDATE` or `DELETE` privileges granted to any application role. Compaction and archival are operational tasks handled by a separate cron job using a separate role.

A weekly review of audit rows with `validation_status = 'rejected'` is part of the operational rota. These are the most informative events in the system. A pattern of rejections in a particular check usually means either the catalogue has a bug or the model has discovered a new way to produce invalid SQL.

## The red-team test set

`backend/tests/unit/test_guard_redteam.py` contains forty injection attempts. The guard must reject all of them. The set covers:

- **Direct destructive statements.** `DELETE FROM claims`, `DROP TABLE members`, `TRUNCATE audit_log`.
- **Stacked statements.** `SELECT 1; DROP TABLE claims`, `SELECT 1; INSERT INTO ...`.
- **Comment-hidden payloads.** `SELECT 1 -- ; DROP TABLE claims`, `/* */ DROP TABLE`.
- **Quoted-identifier tricks.** `SELECT 1 FROM "pg_authid"`, `SELECT 1 FROM "claims"; DROP`.
- **Schema enumeration.** `SELECT table_name FROM information_schema.tables`, `\dt` equivalents.
- **Function abuse.** `SELECT pg_read_file('/etc/passwd')`, `SELECT dblink_exec(...)`, `SELECT lo_import(...)`.
- **Subquery escapes.** Subqueries that reference disallowed tables, subqueries with their own destructive payload.
- **Unicode tricks.** Zero-width spaces, lookalike characters, hex-encoded identifiers.
- **Boolean blind injection patterns.** `WHERE 1=1 AND (SELECT ...)` patterns testing the predicate path.
- **Time-based patterns.** `pg_sleep(...)` and similar.

CI runs the red-team set on every commit. A failure here is a release blocker.

## What this model does not protect against

Honest scope limits. Vellum-NLQ does not protect against:

1. **A compromised catalogue YAML.** If an attacker can edit `catalogues/health-uk/tables.yaml` and add a sensitive table to the allowlist, the guard will accept queries against that table. This is why catalogue changes go through pull request review.

2. **A compromised application server.** If the application binary is replaced, none of these controls apply. This is a deployment-layer concern handled by container immutability and image signing, neither of which is implemented in version one.

3. **Network-level threats.** The application assumes a trusted network between itself and Postgres. TLS to the database is configured but not enforced in version one.

4. **Resource exhaustion.** The fifteen-second statement timeout and ten-thousand-row cap protect against single expensive queries. A flood of inexpensive queries from a malicious client is not addressed. Rate limiting is a documented extension.

5. **Side-channel inference.** A motivated attacker can in principle infer information about the data by observing latency, row counts, and clarification patterns across many queries. This is not addressed and is probably not addressable for an interactive analytics system.

These gaps are documented honestly because pretending otherwise would be worse than disclosing them.

## How to test the safety model yourself

A reviewer who wants to test the safety claims directly can do so.

```bash
make up
# In another terminal:
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Drop all claims"}'
# Returns clarification

make test-redteam
# Runs the forty injection attempts. All must be rejected.

docker exec -it vellum-postgres psql -U vellum_reader -d vellum -c "DELETE FROM claims;"
# Returns: ERROR: permission denied for table claims
```

The first command shows the guard rejecting a malicious question through the API. The second shows the red-team set passing. The third shows the database role rejecting a destructive statement directly, bypassing the application entirely.

Three layers. Each one tested independently. That is the safety model.
