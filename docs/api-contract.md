# API Contract

This document describes the API surface that exists in the current phased build.
The OpenAI intent layer and production Postgres execution path are not active yet.

Base URL for local development:

```text
http://localhost:8000
```

## Product Endpoint

### POST `/ask`

Runs the first product-facing ask flow. The endpoint resolves a question, blocks
unsafe intent when needed, asks for clarification when the metric is ambiguous,
and executes the deterministic demo path when a supported metric is resolved.

Request:

```json
{
  "question": "What was incurred loss ratio in Q1?",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "plan_tier": "Comprehensive"
}
```

Answer response, trimmed to the fields most relevant to the UI:

```json
{
  "status": "answer",
  "question": "What was incurred loss ratio in Q1?",
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
  "answer": {
    "query_id": "q_<uuid>",
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

Clarification response, trimmed to the fields most relevant to the UI:

```json
{
  "status": "clarification_required",
  "question": "How are the claims numbers looking?",
  "message": "Multiple catalogue metrics may answer this question.",
  "resolved_request": null,
  "safety": null,
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
  "question": "Drop all claims from the database.",
  "message": "Request refused. Destructive database operations are not allowed.",
  "resolved_request": null,
  "candidates": [],
  "answer": null,
  "safety": {
    "rule_id": "DDL_DROP_PATTERN",
    "severity": "critical",
    "reason": "Question contains destructive DROP intent."
  }
}
```

## Demo Examples

### GET `/ask/examples`

Returns the nine golden demo questions used by tests and future frontend demo
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
      "version": "0.1.0",
      "last_reviewed": "2026-05-22"
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
  "plan_tier": "Comprehensive"
}
```

Response includes:

- `query_id`
- `metric_id`
- parameterised `sql`
- bound `parameters`
- `provenance`
- SQL guard `validation`

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

Current execution mode is `local_demo`. It does not run against production data.

Supported deterministic metrics in this phase:

- `loss_ratio`
- `paid_claims`

### GET `/queries/{query_id}`

Reads one local JSONL audit event by query ID.

```json
{
  "query_id": "q_<uuid>",
  "event_type": "query_execute",
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
2. The SQL guard validates generated SQL before execution.

`POST /ask` and `POST /queries/execute` do not accept arbitrary SQL. They only
execute SQL generated by the deterministic planner for supported catalogue
paths.

## Audit Notes

Successful preview and execution requests write local JSONL audit events. The
audit record includes request payload, SQL, bound parameters, provenance,
validation outcome, and execution summary when applicable. This is a development
audit store until the Postgres audit table is built.
