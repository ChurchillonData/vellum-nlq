# Demo Script

This document is the runbook for demonstrating Vellum-NLQ. It contains both the
target portfolio demo and the current backend demo boundary.

## Implementation Status

Current backend supports:

- Happy-path answer for `loss_ratio`.
- Happy-path answers for `paid_claims`, `claim_frequency`, `incurred_claims`,
  `claim_severity`, and ungrouped `decline_rate`.
- Grouped decline-rate answer by consultant specialty.
- Grouped outputs by plan tier and member region for supported metrics.
- Ambiguity response for broad claims questions.
- Out-of-scope response for forecasting questions.
- Safety rejection for destructive database requests.
- Backend-v1 natural-language parsing for quarters, ISO date ranges, relative
  demo periods, full-year phrases, demo plan tiers, and supported grouping
  phrases.
- A date-range-required state when the metric is clear but the period is not.
- Provenance payloads with SQL, parameters, validation, and query IDs.
- OpenAI intent extraction behind configuration, with catalogue sanitization and
  deterministic fallback.
- Guarded Postgres execution behind configuration.

Current backend does not yet support:

- Live Postgres integration tests in this execution environment.
- A partner data mapping layer for insurer-specific schemas.
- The large portfolio demo dataset and performance-tuning pass.

Current frontend supports the Ask workspace, Catalogue Explorer, backend-backed
demo examples, and live `/ask` state rendering with saved demo fallback when the
API is unavailable.

The five-question script below is still the target demo arc. For today, use the
current API examples for live verification.

## Current API Demo

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Useful endpoints:

- `GET /ask/examples`
- `POST /ask`
- `GET /metrics`
- `POST /queries/preview`
- `POST /queries/execute`

The current `/ask` endpoint can infer supported quarter phrases, ISO date
ranges, relative demo periods, full-year phrases, demo plan tiers, and supported
grouping phrases. Explicit structured dates and filters are still accepted and
take priority over inferred values.

Example happy path:

```json
{
  "question": "What was loss ratio for the Comprehensive plan tier in Q1 2026?"
}
```

Example ambiguity:

```json
{
  "question": "How are the claims numbers looking?",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31"
}
```

Example out-of-scope:

```json
{
  "question": "What will loss ratio be next quarter?",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31"
}
```

Example safety rejection:

```json
{
  "question": "Drop all claims from the database"
}
```

## Target Demo Arc

The final portfolio demo should run in under three minutes. The order matters
because each question proves a different property of the system.

1. Happy path. Show the system works.
2. Grouping. Show the planner handles joins and aggregation correctly.
3. Ambiguity. Show the system asks rather than guesses.
4. Out of scope. Show the system knows what it does not do.
5. Adversarial. Show the safety model refuses unsafe requests.

## Target Script

### Opening

Say:

"Vellum-NLQ is a controlled natural-language query layer for UK private medical
insurance claims. It answers business questions in plain English, generates SQL
against a fixed schema, validates the SQL before execution, and shows the audit
trail on every answer."

### Question 1: Happy Path

Ask:

```text
What was loss ratio for the Comprehensive plan tier in Q1 2026?
```

Show the summary, metric definition, generated SQL, validation status, and
query ID.

### Question 2: Grouping

Ask:

```text
Decline rate by consultant specialty for the last six months
```

Current behaviour: grouped result table sorted by decline rate, with catalogue
join provenance and a guarded 50-row result limit.

### Question 3: Ambiguity

Ask:

```text
How are the claims numbers looking?
```

Target behaviour: structured clarification with candidate metrics such as loss
ratio, paid claims, and claim frequency.

### Question 4: Out Of Scope

Ask:

```text
What will loss ratio be next quarter?
```

Target behaviour: forecast refusal with a clear out-of-scope reason.

### Question 5: Adversarial

Ask:

```text
Drop all claims from the database
```

Target behaviour: blocked state with rule ID, no SQL compilation, and audit
trace.

The current red-team suite can also be shown:

```bash
make test-redteam
```

and a direct database permission check using the read-only role.

## What To Do When Something Breaks

- If the resolver asks for clarification, show the clarification state honestly.
- If seeded data is not ready, use the API preview path instead of execution.
- If the frontend is not ready, demonstrate through `/docs` or `curl`.
- If safety tests fail, stop and fix them before recording.

## Closing Thought

The most important demo moment is not the happy path. It is the moment the
system refuses to guess or refuses to run unsafe work. That is what makes this a
governed analytics product rather than a generic text-to-SQL toy.
