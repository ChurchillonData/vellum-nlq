# Safety Model

This document explains the current Vellum-NLQ safety boundary and separates it
from the target production model.

## Implementation Status

Current build:

- User questions with destructive database intent are blocked before planning.
- Generated SQL is parsed before execution.
- The SQL guard accepts one SELECT statement only.
- Comments, stacked statements, non-SELECT statements, and system schema
  references are rejected.
- Tables, columns, functions, and join paths are checked against the active
  semantic catalogue.
- Every `/ask` outcome writes a local JSONL audit event, including blocked,
  clarification, date-range-required, out-of-scope, and answer states.
- Successful previews and local demo executions also write local JSONL audit
  events.
- The first red-team suite covers destructive user intent and unsafe SQL guard
  cases.

Not built yet:

- Postgres read-only execution for product requests.
- Append-only Postgres audit table.
- Expanded red-team coverage for prompt injection and obfuscated attacks.
- Result row caps enforced by the guard.
- Parameter literal enforcement in the guard.

## Product Boundary

Vellum-NLQ is a governed analytics reader. It supports SELECT-only analytics
queries. It is not a database administration tool and it is not allowed to run
mutable commands.

This is a deliberate product decision. The LLM, when introduced, will not be
the database driver. It will be one layer inside a governed workflow:

1. The resolver interprets intent.
2. The catalogue decides what is answerable.
3. The planner builds a supported analytics path.
4. The generator emits parameterised SQL.
5. The guard validates the final SQL before execution.

## Layer 1: Question Safety

Before planning begins, the resolver checks for obviously unsafe database
intent. Requests such as "drop all claims", "delete members", or "truncate the
premium table" are returned as blocked states with a safety rule ID.

This early layer exists for user experience and audit clarity. It is not the
only safety layer.

## Layer 2: SQL Guard

The SQL guard receives generated SQL and validates it before execution. The
current checks are intentionally small and readable:

1. SQL must parse successfully.
2. Exactly one statement is allowed.
3. The statement must be SELECT.
4. SQL comments are rejected.
5. System schemas such as `information_schema` and `pg_catalog` are rejected.
6. Referenced tables must be in the catalogue allowlist.
7. Referenced columns must be in the catalogue allowlist.
8. Referenced functions must be in the function allowlist.
9. Join paths must match the catalogue join graph.

The current function allowlist is deliberately narrow:

- `CAST`
- `COUNT`
- `NULLIF`
- `SUM`

When a legitimate metric requires a new function, it should be added with a
small test and a clear reason.

## Layer 3: Audit Trail

The current build writes local JSONL audit events for every `/ask` outcome.
That means answer, clarification, blocked, date-range-required, and out-of-scope
states all receive a query ID and can be loaded through the audit lookup
endpoint. Successful preview and demo execution requests are also audited.

For answer, preview, and execution events, the event includes SQL, bound
parameters, provenance, and validation result. For blocked, clarification, and
out-of-scope states, the event records the status and the relevant safety,
candidate, or scope payload instead of pretending SQL exists.

This is useful for the demo backend and for development. It is not the final
audit design.

The target production design keeps this same product behaviour but moves the
store to an append-only Postgres audit table.

## Target Production Controls

The full target system will add:

- A Postgres role with SELECT-only permissions.
- Database-level statement timeout.
- Append-only audit table.
- Expanded red-team tests for injection and schema-exfiltration attempts.
- Integration tests against seeded Postgres data.
- Result-size limits.
- Clear operational review of rejected queries.

These are documented as roadmap items so the safety story stays honest while
the project is built in phases.

## How To Test The Current Safety Boundary

Run the unit tests:

```bash
cd backend
python -m pytest tests/unit -q
```

Run the current red-team suite:

```bash
cd backend
python -m pytest tests/redteam -q
```

Try a blocked request through the API:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Drop all claims from the database\"}"
```

Expected result: a structured blocked response, not generated SQL.

## What This Model Does Not Protect Against Yet

Honest scope limits:

1. A compromised catalogue YAML file can widen the allowlist.
2. The current demo execution path is SQLite-backed, not Postgres-backed.
3. The current audit log is local JSONL, not a database-enforced append-only
   table.
4. Red-team coverage is still a first slice and does not yet include
   obfuscated or encoded prompt-injection attempts.
5. Rate limiting and side-channel inference controls are not implemented yet.

These gaps are build-plan items, not hidden assumptions.
