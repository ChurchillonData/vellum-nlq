# Vellum-NLQ

A controlled natural-language query layer for UK private medical insurance claims data.

> Implementation note: this repository is being built in phases. The overview
> documents describe the target system, while `docs/BUILD_PLAN.md` tracks what
> is implemented today and what remains.

[![Catalogue](https://img.shields.io/badge/catalogue-health--uk-blue)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

Vellum-NLQ answers governed analytics questions by resolving intent against a
semantic catalogue, generating parameterised SQL, validating that SQL before
execution, and returning the answer with provenance.

It is not a chatbot. It is a narrow, auditable analytics interface for a
regulated domain where wrong numbers cause real harm.

## Current Build

The current backend is a deterministic demo slice. It does not call OpenAI yet
and does not execute against Postgres yet.

Implemented today:

- FastAPI backend with product-facing `/ask` and development query endpoints.
- Catalogue-backed deterministic paths for all six current metrics:
  `loss_ratio`, `paid_claims`, `claim_frequency`, `decline_rate`,
  `incurred_claims`, and `claim_severity`.
- Grouped `decline_rate` by consultant specialty.
- Result-size controls for grouped outputs, with guarded row limits surfaced in
  provenance and audit records.
- Narrow natural-language parsing for quarter phrases, ISO date ranges, and
  demo plan tiers on `POST /ask`.
- Ambiguity, out-of-scope, and destructive-intent responses for controlled demo
  questions.
- SQL generation and guard validation for generated SELECT statements.
- Catalogue-backed table, column, function, and join-path validation.
- In-memory SQLite demo execution seeded from synthetic data.
- Local JSONL audit events for all `/ask` outcomes, successful previews, and
  demo executions.
- Seventeen `/ask/examples` items covered by unit tests.
- YAML golden question suite covering the core demo contract.
- First red-team suite for destructive questions and unsafe SQL guard cases.

Planned next:

- OpenAI structured intent extraction behind a narrow provider interface.
- Richer natural-language date and filter parsing.
- Postgres read-only execution and append-only audit table.
- Expanded red-team coverage for obfuscated and prompt-injection-style attacks.
- Frontend implementation using the uploaded UI mockups.

## Five-Minute Tour

If you have five minutes, read these files in this order.

1. `backend/catalogues/health-uk/metrics/loss_ratio.yaml` - what a metric
   definition looks like.
2. `backend/catalogues/health-uk/joins.yaml` - the join graph the planner and
   guard use.
3. `backend/app/sql/guard.py` - the SQL validation boundary.
4. `backend/app/ask/examples.py` - the current demo examples used by tests.
5. `docs/DECISIONS.md` - the architectural decisions and what was rejected.

That tour shows what the current backend can answer, what it refuses, and why.

## What It Does

A claims analyst asks a governed analytics question. The system resolves it
against a typed semantic catalogue, builds a logical plan, generates
parameterised SQL, validates the SQL, and returns the answer with provenance.

Five things make this different from a generic text-to-SQL demo.

1. **A semantic catalogue, not prompt engineering.** Metrics are defined in YAML
   with explicit formulas, time anchors, owners, and version numbers.
2. **A SELECT-only product boundary.** Vellum-NLQ is an analytics reader, not a
   database driver. Mutable SQL is outside the product.
3. **Catalogue-backed SQL safety.** Generated SQL is checked against table,
   column, function, and join allowlists before execution.
4. **Clarification before guessing.** Ambiguous, unsupported, and out-of-scope
   questions return structured states rather than confident wrong answers.
5. **Provenance first.** Answers include metric details, SQL, parameters,
   validation outcome, and a query ID.

## Why It Exists

This project is a prototype of the analytics surface I am building for Govaxis,
a UK claims intelligence platform for health insurers. It is also a portfolio
demonstration of AI system design for regulated analytics.

Claims teams need numbers they can defend in front of regulators, auditors, and
underwriters. Today they often get those numbers by writing tickets to a small
analytics team and waiting. Vellum-NLQ explores a faster path with explicit
controls.

## Quick Start

Install backend dependencies, then run the current test suite.

```bash
cd backend
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
```

Run the API locally.

```bash
cd backend
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/docs`.

## Repository Layout

```text
vellum-nlq/
|-- README.md
|-- docs/
|   |-- BUILD_PLAN.md
|   |-- CODEBASE_STANDARDS.md
|   |-- DECISIONS.md
|   |-- api-contract.md
|   |-- demo-script.md
|   |-- adding-a-metric.md
|   `-- safety-model.md
|-- design-mockups/
|   `-- frontend/
|-- database/
|-- backend/
|   |-- app/
|   |   |-- analytics/
|   |   |-- api/
|   |   |-- ask/
|   |   |-- audit/
|   |   |-- execution/
|   |   |-- planner/
|   |   |-- semantic/
|   |   `-- sql/
|   |-- catalogues/
|   |   `-- health-uk/
|   |-- seeds/
|   `-- tests/
|       |-- redteam/
|       |-- golden/
|       `-- unit/
`-- Makefile
```

Frontend, integration tests, red-team tests, and production Postgres execution
are planned phases, not finished implementation.

## The Catalogue

Vellum-NLQ is multi-catalogue by design. The current build includes the
`health-uk` catalogue slice.

| Metric | Catalogue status | Executable today |
|---|---:|---:|
| `loss_ratio` | Yes | Yes |
| `paid_claims` | Yes | Yes |
| `claim_frequency` | Yes | Yes |
| `decline_rate` | Yes | Yes |
| `incurred_claims` | Yes | Yes |
| `claim_severity` | Yes | Yes |

Adding a new metric should start with catalogue YAML, tests, and a narrow
planner/generator path. The codebase intentionally favours small readable files
over one large clever pipeline.

## Safety Model

The current SQL guard checks:

1. SQL parses successfully.
2. Exactly one statement is present.
3. The statement is SELECT-only.
4. Comments are absent.
5. System schemas are not referenced.
6. Tables are on the catalogue allowlist.
7. Columns are on the catalogue allowlist.
8. Functions are on the allowlist.
9. Join paths match the catalogue graph.

The current allowlisted functions are deliberately small: `CAST`, `COUNT`,
`NULLIF`, and `SUM`.

Planned safety work includes Postgres read-only role enforcement, a persisted
append-only audit table, expanded red-team coverage, and result-size controls.

Read `docs/safety-model.md` for the current safety boundary and target model.

## Testing

Current reliable test command:

```bash
cd backend
python -m pytest tests/unit -q
```

Golden contract test:

```bash
cd backend
python -m pytest tests/golden -q
```

Red-team safety test:

```bash
cd backend
python -m pytest tests/redteam -q
```

Or from the repo root:

```bash
make test-unit
make test-golden
make test-redteam
```

The current suite covers catalogue loading, deterministic resolution, planning,
SQL generation, SQL guard checks, demo execution, ask audit coverage, audit
lookup, `/ask` examples, the YAML golden question contract, and the first
red-team suite.

## Current API Surface

Full request and response examples are documented in `docs/api-contract.md`.

| Endpoint | Purpose |
|---|---|
| `POST /ask` | Product-facing ask flow. Returns answer, clarification, blocked, or out-of-scope state. |
| `GET /ask/examples` | Seventeen demo questions used by tests and future UI controls. |
| `GET /metrics` | Active catalogue metric definitions with formulas and versions. |
| `POST /queries/resolve` | Deterministic metric resolution and early safety blocking. |
| `POST /queries/preview` | Parameterised SQL and provenance without execution. |
| `POST /queries/execute` | Guarded deterministic demo execution against synthetic local data. |
| `GET /queries/{query_id}` | Local JSONL audit trace for a previous ask, preview, or execution. |
| `GET /health` | Liveness and active catalogue name. |

## What This Proves

If you are reading this as a hiring reviewer, the project is meant to show:

- I understand that the semantic catalogue is the hard part, not the LLM
  plumbing.
- I treat SELECT-only execution as the product boundary.
- I validate generated SQL structurally before it reaches execution.
- I can build in phases without pretending the unfinished parts are done.
- I write tests that double as documentation.

## Author

Owura. Founder of Govaxis. Based in London.

## Licence

MIT.
