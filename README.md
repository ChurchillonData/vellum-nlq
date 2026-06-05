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

The current backend is a governed demo slice. It does not call OpenAI by
default. Local Postgres schema, roles, migrations, seeding, and guarded
Postgres execution are available. The default execution backend remains the
in-memory demo executor until `VELLUM_EXECUTION_BACKEND=postgres` is set.

Implemented today:

- FastAPI backend with product-facing `/ask` and development query endpoints.
- React + Vite frontend shell for the Ask workspace, Catalogue Explorer, and
  Audit view.
- Catalogue-backed deterministic paths for twelve governed insurance metrics:
  `loss_ratio`, `paid_claims`, `claim_frequency`, `decline_rate`,
  `incurred_claims`, `claim_severity`, `claim_count`, `covered_members`,
  `open_claim_rate`, `out_of_network_rate`, `premium_per_member`, and
  `case_reserves`.
- Grouped `decline_rate` by consultant specialty.
- Result-size controls for grouped outputs, with guarded row limits surfaced in
  provenance and audit records.
- OpenAI intent-provider boundary behind configuration. OpenAI may propose
  structured intent, but Vellum still owns catalogue resolution, SQL generation,
  guard validation, execution, and audit.
- OpenAI intent output is sanitized against the catalogue, confidence-gated,
  and can fall back to deterministic parsing.
- Backend-v1 natural-language parsing for quarters, natural dates, month names,
  month ranges, ISO date ranges, relative demo periods, full-year phrases, plan
  tiers, and supported grouping phrases.
- Rolling demo data for the last 18 completed months, with future or unavailable
  historical periods rejected before SQL planning.
- Grouped demo outputs for plan tier and region across supported metrics, plus
  decline rate by consultant specialty.
- Ambiguity, out-of-scope, and destructive-intent responses for controlled demo
  questions.
- SQL generation and guard validation for generated SELECT statements.
- Catalogue-backed table, column, function, and join-path validation.
- In-memory SQLite demo execution seeded from synthetic data.
- Local Postgres Docker setup with admin, seeder, and read-only roles.
- Alembic migration and seed command for deterministic synthetic data.
- Configurable execution backend: local demo by default, Postgres through the
  read-only URL when enabled.
- Local Postgres proof workflow for start, migrate, role check, seed, smoke,
  and optional integration verification.
- Portfolio seed dry run that previews the 200,000-member load plan and
  table-level row counts without touching Postgres.
- Partner schema mapping validator with a fictional insurer mapping example.
- Local JSONL audit events for all `/ask` outcomes, successful previews, and
  demo executions.
- Append-only Postgres audit table behind `VELLUM_AUDIT_BACKEND=postgres`.
- Twenty-six `/ask/examples` items covered by unit tests.
- YAML golden question suite covering the core demo contract.
- First red-team suite for destructive questions and unsafe SQL guard cases.
- Scripted five-step demo command that runs the product `/ask` flow end to end.
- GitHub Actions CI for backend unit, golden, red-team, optional integration
  suite import checks, and frontend production build.

Planned next:

- Browser-verified frontend polish against live backend responses.
- Hosted deployment and runtime use of partner mappings after a private insurer
  schema is available.

## Five-Minute Tour

If you have five minutes, read these files in this order.

1. `backend/catalogues/health-uk/metrics/loss_ratio.yaml` - what a metric
   definition looks like.
2. `backend/catalogues/health-uk/joins.yaml` - the join graph the planner and
   guard use.
3. `backend/app/sql/guard.py` - the SQL validation boundary.
4. `backend/app/ask/examples.py` - the current demo examples used by tests.
5. `docs/local-postgres.md` - how the local database foundation works.
6. `docs/schema-mapping.md` - how a partner insurer schema maps to Vellum.
7. `docs/DECISIONS.md` - the architectural decisions and what was rejected.

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

OpenAI can be enabled for intent extraction with `VELLUM_INTENT_PROVIDER=openai`
and `VELLUM_OPENAI_API_KEY`. The model is not allowed to return SQL; it only
proposes structured fields such as metric, date range, plan tier, grouping, and
confidence.

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

Run the frontend locally.

```bash
cd frontend
npm install
npm run dev
```

Then open `http://127.0.0.1:5173`. Set `VITE_API_BASE_URL` if the backend runs
somewhere other than `http://127.0.0.1:8000`.

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
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- api.ts
|   |   `-- App.tsx
`-- Makefile
```

Live Postgres integration tests are implemented as an optional suite because
they require a seeded database. Generated portfolio quality checks are
implemented; hosted production deployment remains a planned phase.

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
| `claim_count` | Yes | Yes |
| `covered_members` | Yes | Yes |
| `open_claim_rate` | Yes | Yes |
| `out_of_network_rate` | Yes | Yes |
| `premium_per_member` | Yes | Yes |
| `case_reserves` | Yes | Yes |

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

Future safety work should keep expanding red-team cases as new metrics and
dimensions ship. A hosted deployment still needs an operational security
review before any external production use.

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
make security-audit
```

Run the guided five-step product demo:

```bash
make demo
```

On Windows without Make:

```powershell
cd backend
python -m app.demo.runner
```

Optional live Postgres integration test:

```bash
cd backend
VELLUM_RUN_POSTGRES_INTEGRATION=1 python -m pytest tests/integration -q
```

The integration test expects a migrated and seeded Postgres database plus the
configured admin, seeder, read-only, and auditor URLs.

Run the full local Postgres proof workflow:

```bash
make postgres-proof
```

On Windows without Make:

```powershell
python scripts/prove_postgres.py --seed local --integration
```

To verify an already seeded database without loading new data:

```powershell
python scripts/prove_postgres.py --skip-start
```

The current suite covers catalogue loading, deterministic resolution, planning,
SQL generation, SQL guard checks, demo execution, ask audit coverage, audit
lookup, `/ask` examples, the YAML golden question contract, and the first
red-team suite. The optional integration suite verifies the seeded Postgres
execution path when a real database is available.

GitHub Actions runs the implemented backend test suites, checks that the
optional integration suite skips cleanly without a live database, and builds
the frontend on pushes to `main` and on pull requests.

## Current API Surface

Full request and response examples are documented in `docs/api-contract.md`.

| Endpoint | Purpose |
|---|---|
| `POST /ask` | Product-facing ask flow. Returns answer, clarification, blocked, or out-of-scope state. |
| `GET /ask/examples` | Twenty-six demo questions used by tests and future UI controls. |
| `GET /metrics` | Active catalogue metric definitions with formulas and versions. |
| `GET /mappings/{partner}/coverage` | Validated partner schema mapping coverage. |
| `POST /queries/resolve` | Deterministic metric resolution and early safety blocking. |
| `POST /queries/preview` | Parameterised SQL and provenance without execution. |
| `POST /queries/execute` | Guarded deterministic demo execution against synthetic local data. |
| `GET /queries/{query_id}` | Audit trace for a previous ask, preview, or execution. |
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
