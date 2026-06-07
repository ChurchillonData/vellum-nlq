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
- Embedded string and date literals are rejected so request values stay bound as
  parameters.
- Grouped SQL must include an approved row limit. The current grouped cap is 50
  rows.
- OpenAI, when enabled, only proposes structured intent. It does not generate
  SQL or execute queries.
- OpenAI output is sanitized against the catalogue and confidence-gated before
  the resolver can use it.
- Every `/ask` outcome writes a local JSONL audit event, including blocked,
  clarification, date-range-required, out-of-scope, and answer states.
- Successful previews and local demo executions also write local JSONL audit
  events.
- `VELLUM_AUDIT_BACKEND=postgres` writes the same event shape to an
  append-only `audit_events` table.
- The red-team suite covers destructive user intent, delete-like synonyms,
  prompt-injection-style destructive requests, and unsafe SQL guard cases.

Not built yet:

- Optional live Postgres integration tests for execution and audit.
- Expanded red-team coverage for prompt injection and obfuscated attacks.

## Product Boundary

Vellum-NLQ is a governed analytics reader. It supports SELECT-only analytics
queries. It is not a database administration tool and it is not allowed to run
mutable commands.

This is a deliberate product decision. The LLM is not the database driver. It is
one layer inside a governed workflow:

1. The resolver interprets intent.
2. The catalogue decides what is answerable.
3. The planner builds a supported analytics path.
4. The generator emits parameterised SQL.
5. The guard validates the final SQL before execution.

When OpenAI is enabled, it sits before step 1 as an intent proposer only. The
system discards unknown provider values instead of expanding the executable
surface.

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
9. String and date values must be supplied as bound parameters.
10. Join paths must match the catalogue join graph.
11. Grouped result sets must have an approved row limit.

The current function allowlist is deliberately narrow:

- `CAST`
- `COUNT`
- `DATE_TRUNC`
- `NULLIF`
- `SUM`
- `TIMESTAMP_TRUNC`

When a legitimate metric requires a new function, it should be added with a
small test and a clear reason.

## Layer 3: Audit Trail

The current build writes audit events for every `/ask` outcome.
That means answer, clarification, blocked, date-range-required, and out-of-scope
states all receive a query ID and can be loaded through the audit lookup
endpoint. Successful preview and demo execution requests are also audited.

For answer, preview, and execution events, the event includes SQL, bound
parameters, provenance, and validation result. For blocked, clarification, and
out-of-scope states, the event records the status and the relevant safety,
candidate, or scope payload instead of pretending SQL exists.

The default store is local JSONL so the backend runs without Docker. When
`VELLUM_AUDIT_BACKEND=postgres` is set, the same records are written to the
append-only `audit_events` table through a local role with SELECT and INSERT
grants only.

## Target Production Controls

The full target system will add:

- A Postgres role with SELECT-only permissions.
- Database-level statement timeout.
- Expanded red-team tests for injection and schema-exfiltration attempts.
- Integration tests against seeded Postgres data.
- Broader result-size policies as more grouped dimensions are added.
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
2. Live Postgres integration tests require a migrated and seeded database, so
   they run only when explicitly enabled.
3. Red-team coverage is still a first slice and does not yet include
   obfuscated or encoded prompt-injection attempts.
4. Rate limiting and side-channel inference controls are not implemented yet.

These gaps are build-plan items, not hidden assumptions.
