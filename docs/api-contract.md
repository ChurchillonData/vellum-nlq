# API Contract

This document describes the API surface that exists in the current phased build.
The OpenAI intent provider boundary is available behind configuration. Guarded
Postgres execution is available behind `VELLUM_EXECUTION_BACKEND=postgres`.

Base URL for local development:

```text
http://localhost:8000
```

## Product Endpoint

### POST `/ask`

Runs the first product-facing ask flow. The endpoint resolves a question, infers
supported date ranges, plan-tier filters, and the first supported grouping from
the question when possible, blocks unsafe intent when needed, asks for
clarification when the metric is ambiguous, and executes the deterministic demo
path when a supported metric is resolved.

When `VELLUM_INTENT_PROVIDER=openai`, OpenAI may propose structured intent
fields. It does not generate SQL. The proposed intent still passes through the
catalogue, deterministic planner, SQL generator, SQL guard, demo execution, and
audit path.

OpenAI output is treated as untrusted input. Unknown metric IDs, unsupported
plan tiers, unsupported groupings, and low-confidence proposals are discarded
before the resolver runs. If the OpenAI provider is unavailable, Vellum falls
back to deterministic parsing by default.

Request:

```json
{
  "question": "What was loss ratio for the Comprehensive plan tier in Q1 2026?"
}
```

Explicit `metric_id`, `start_date`, `end_date`, `plan_tier`, and `group_by`
fields are still accepted. When provided, explicit fields win over inferred
values. `metric_id` is used by the frontend after a clarification selection; it
must still name a catalogue metric, and it still passes through deterministic
planning, SQL guard validation, execution, and audit.

Supported inference in this phase:

- `Q1 2026`, `Q2 2026`, `Q3 2026`, `Q4 2026`
- `2026 Q1`, `2026 Q2`, `2026 Q3`, `2026 Q4`
- two ISO dates such as `2026-01-01` and `2026-03-31`
- plan tiers: `Essential`, `Comprehensive`, `Executive`
- grouping phrase: `by consultant specialty`

Answer response, trimmed to the fields most relevant to the UI:

```json
{
  "status": "answer",
  "query_id": "q_<uuid>",
  "question": "What was loss ratio for the Comprehensive plan tier in Q1 2026?",
  "message": "Resolved to metric: loss_ratio.",
  "resolved_request": {
    "metric_id": "loss_ratio",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
    "plan_tier": "Comprehensive"
  },
  "candidates": [
    {
      "metric_id": "loss_ratio",
      "label": "Loss ratio",
      "confidence": 0.9,
      "reason": "synonym matched: incurred loss ratio"
    }
  ],
  "safety": null,
  "scope": null,
  "answer": {
    "query_id": "q_<same uuid>",
    "metric_id": "loss_ratio",
    "answer": "<computed natural-language summary>",
    "row_count": 1,
    "execution_mode": "local_demo",
    "rows": [
      {
        "loss_ratio": 0.04882407281207881
      }
    ]
  }
}
```

The `provenance.result_shape` object includes `columns`, `grain`, and
`max_rows`. Ungrouped metrics currently have `max_rows: 1`. Grouped
`decline_rate by consultant_specialty` has `max_rows: 50`.

If a question resolves to a supported metric but no date range is provided or
inferred, the endpoint returns a date-range prompt:

```json
{
  "status": "date_range_required",
  "query_id": "q_<uuid>",
  "question": "What was loss ratio for the Comprehensive plan tier?",
  "message": "A supported date range is required before planning SQL.",
  "resolved_request": null,
  "answer": null
}
```

Clarification response, trimmed to the fields most relevant to the UI:

```json
{
  "status": "clarification_required",
  "query_id": "q_<uuid>",
  "question": "How are the claims numbers looking?",
  "message": "Multiple catalogue metrics may answer this question.",
  "resolved_request": null,
  "safety": null,
  "scope": null,
  "answer": null,
  "candidates": [
    {
      "metric_id": "loss_ratio",
      "label": "Loss ratio",
      "confidence": 0.42,
      "reason": "ambiguous claims question"
    },
    {
      "metric_id": "paid_claims",
      "label": "Paid claims",
      "confidence": 0.42,
      "reason": "ambiguous claims question"
    },
    {
      "metric_id": "claim_frequency",
      "label": "Claim frequency",
      "confidence": 0.42,
      "reason": "ambiguous claims question"
    }
  ]
}
```

Blocked response:

```json
{
  "status": "blocked",
  "query_id": "q_<uuid>",
  "question": "Drop all claims from the database.",
  "message": "Request refused. Destructive database operations are not allowed.",
  "resolved_request": null,
  "candidates": [],
  "answer": null,
  "scope": null,
  "safety": {
    "rule_id": "DDL_DROP_PATTERN",
    "severity": "critical",
    "reason": "Question contains destructive DROP intent."
  }
}
```

Out-of-scope response:

```json
{
  "status": "out_of_scope",
  "query_id": "q_<uuid>",
  "question": "What will loss ratio be next quarter?",
  "message": "Request is outside the current analytics scope.",
  "resolved_request": null,
  "candidates": [],
  "answer": null,
  "safety": null,
  "scope": {
    "reason_id": "forecasting_not_supported",
    "reason": "Forecasting questions are outside the current analytics scope."
  }
}
```

## Demo Examples

### GET `/ask/examples`

Returns the twenty golden demo questions used by tests and future frontend demo
controls. Each example has an expected ask state.

```json
{
  "examples": [
    {
      "id": "answer_loss_ratio_q1",
      "label": "Loss ratio in Q1",
      "question": "What was incurred loss ratio in Q1?",
      "expected_status": "answer",
      "start_date": "2026-01-01",
      "end_date": "2026-03-31",
      "plan_tier": "Comprehensive"
    }
  ]
}
```

The unit suite sends every returned example back through `POST /ask`.

The YAML golden contract lives at `backend/tests/golden/questions.yaml` and is
run with:

```bash
cd backend
python -m pytest tests/golden -q
```

## Catalogue

### GET `/metrics`

Returns metric definitions from the active semantic catalogue.

```json
{
  "catalogue": "health-uk",
  "metrics": [
    {
      "id": "loss_ratio",
      "label": "Loss ratio",
      "description": "Incurred claims divided by earned premium for the selected reporting slice.",
      "formula": {
        "numerator": "SUM(claims.net_incurred_amount)",
        "denominator": "SUM(premium.earned_amount)",
        "expression": "SUM(claims.net_incurred_amount) / NULLIF(SUM(premium.earned_amount), 0)"
      },
      "required_tables": ["claims", "premium"],
      "time_anchor": "claims.incurred_date",
      "currency": null,
      "filters_default": ["claims.status != 'void'"],
      "synonyms": ["loss ratio", "incurred loss ratio"],
      "owner": "actuarial",
      "version": "Vellum 2.5",
      "last_reviewed": "2026-05-22",
      "allowed_dimensions": ["plan_tier", "region"],
      "join_preview": [
        "claims.member_id -> members.id (many_to_one)",
        "premium.member_id -> members.id (many_to_one)"
      ]
    }
  ]
}
```

## Development Query Endpoints

These endpoints expose the internal deterministic pieces separately. The
frontend should prefer `POST /ask` for the product workflow.

### POST `/queries/resolve`

Runs deterministic metric resolution and early safety blocking without SQL
generation or execution.

Request:

```json
{
  "question": "How are the claims numbers looking?",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31"
}
```

Response has the same resolution fields as `/ask`, without the `answer` field.

### POST `/queries/preview`

Builds parameterised SQL and provenance without executing the query.

Request:

```json
{
  "metric_id": "loss_ratio",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "plan_tier": "Comprehensive",
  "group_by": []
}
```

Current grouped request:

```json
{
  "metric_id": "decline_rate",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "group_by": ["consultant_specialty"]
}
```

Response includes:

- `query_id`
- `metric_id`
- parameterised `sql`
- bound `parameters`
- `provenance`
- SQL guard `validation`

`provenance.result_shape.max_rows` is part of the result-size safety contract.

### POST `/queries/execute`

Builds SQL, validates it, and executes the supported deterministic path against
the in-memory synthetic demo dataset.

Request shape matches `/queries/preview`.

Response includes all preview fields plus:

- `answer`
- `rows`
- `row_count`
- `execution_mode`
- `dataset`

Default execution mode is `local_demo`. When
`VELLUM_EXECUTION_BACKEND=postgres`, execution runs guarded generated SQL
against `VELLUM_READONLY_DATABASE_URL`.

Supported deterministic metrics in this phase:

- `loss_ratio`
- `paid_claims`
- `claim_frequency`
- `decline_rate`
- `incurred_claims`
- `claim_severity`

Current grouped deterministic path:

- `decline_rate` by `consultant_specialty`

Grouped rows are shaped as:

```json
[
  {
    "consultant_specialty": "Cardiology",
    "decline_rate": 0.125
  }
]
```

### GET `/queries/{query_id}`

Reads one audit event by query ID. This includes ask outcomes, preview
requests, and execution requests. The default development store is JSONL;
`VELLUM_AUDIT_BACKEND=postgres` reads from the Postgres audit table.

```json
{
  "query_id": "q_<uuid>",
  "event_type": "ask",
  "status": "answer",
  "metric_id": "loss_ratio",
  "sql": "...",
  "parameters": {
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
    "excluded_status": "void",
    "plan_tier": "Comprehensive"
  },
  "validation": {
    "passed": true,
    "rules_checked": ["select_only", "..."],
    "rejections": []
  }
}
```

Returns `404` when the query ID is not found.

## Health

### GET `/health`

Returns liveness and the active catalogue name.

```json
{
  "status": "ok",
  "catalogue": "health-uk"
}
```

## Safety Notes

Vellum-NLQ is intentionally SELECT-only. It is an analytics assistant, not a
database admin tool.

The current build has two safety layers:

1. The question resolver blocks destructive intent before planning.
2. The SQL guard validates generated SQL before execution, including
   parameter-literal checks and grouped result-size controls.

`POST /ask` and `POST /queries/execute` do not accept arbitrary SQL. They only
execute SQL generated by the deterministic planner for supported catalogue
paths.

## Audit Notes

Every `/ask` response writes an audit event, including answer, clarification,
blocked, date-range-required, and out-of-scope states. Successful preview and
execution requests are also audited. The audit record includes the request
payload, status, query ID, SQL and provenance when generated, validation outcome
when available, and execution summary when applicable.

By default, audit records are written to local JSONL for no-Docker development.
When `VELLUM_AUDIT_BACKEND=postgres` is set, records are written to the
append-only `audit_events` table using `VELLUM_AUDIT_DATABASE_URL`.
