# Vellum-NLQ

A controlled natural-language query layer for UK private medical insurance claims data.

> Implementation note: this repository is being built in phases. The overview
> documents describe the target system; `docs/BUILD_PLAN.md` tracks the code path
> from the current foundation to the full demoable product.
> `docs/CODEBASE_STANDARDS.md` records the maintainability rules for implementation.

[![CI](https://img.shields.io/badge/CI-passing-green)]()
[![Catalogue](https://img.shields.io/badge/catalogue-health--uk-blue)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

Vellum-NLQ answers questions like "what was loss ratio for the Comprehensive plan tier in Q1 2026?" by generating SQL against a fixed schema, validating that SQL with an AST walker before execution, and running it on a read-only database role. Every answer ships with the SQL used, the metric definition, the join path traversed, and the validation result.

It is not a chatbot. It is a narrow, auditable analytics interface for a regulated domain where wrong numbers cause real harm.

## Five-minute tour

If you have five minutes, read these files in this order.

1. `backend/catalogues/health-uk/metrics/loss_ratio.yaml` — what a metric definition looks like.
2. `backend/catalogues/health-uk/joins.yaml` — the join graph the planner traverses.
3. `backend/app/sql/guard.py` — the eleven checks that run on every generated SQL string.
4. `backend/tests/golden/questions.yaml` — the approved question set CI runs on every commit.
5. `docs/DECISIONS.md` — the architectural decisions and what was rejected.

That tour tells you what this system does, what it refuses to do, and why.

## What it does

A claims analyst asks a question in plain English. The system extracts the intent, resolves it against a typed semantic catalogue, generates parameterised SQL, validates the SQL against an allowlist, runs it on a read-only role, and returns the answer with full provenance.

Five things make this different from a generic text-to-SQL demo.

1. **A semantic catalogue, not prompt engineering.** Metrics are defined in YAML with explicit formulas, time anchors, and version numbers. The model proposes intent. The catalogue decides what the system can answer.
2. **An AST-level SQL guard.** SQL is parsed with SQLGlot and walked against a table allowlist, a column allowlist, a function allowlist, and a join graph before execution. The database connects on a read-only role as a second line of defence.
3. **Clarification before guessing.** Ambiguous, unsupported, and out-of-scope questions get a structured clarification, not a confident wrong answer.
4. **Audit on every request.** Every question, intent, SQL string, validation outcome, row count, and latency is logged before the response returns.
5. **Multi-catalogue by design.** Version one ships the health-uk catalogue only. Adding motor-uk or property-uk is a configuration exercise, not a code change.

## Why it exists

This project is a prototype of the analytics surface I am building for Govaxis, a UK claims intelligence platform for health insurers. It is also an honest demonstration that I understand the parts of building AI systems for regulated industries that most portfolio projects skip.

Claims teams need numbers they can defend in front of regulators, auditors, and underwriters. Today they get those numbers by writing tickets to a small analytics team and waiting two to five days. Vellum-NLQ replaces the slow lane with a fast lane that has the same controls.

## Quick start

```bash
git clone https://github.com/owura/vellum-nlq
cd vellum-nlq
make seed     # Builds containers, runs migrations, seeds data, loads catalogue
make up       # Starts backend, frontend, and Postgres
```

Open `http://localhost:5173` and ask "what was loss ratio for the Comprehensive plan tier in Q1 2026?"

## Repository layout

```
vellum-nlq/
├── README.md
├── docs/
│   ├── BUILD_PLAN.md                 # Phased implementation plan
│   ├── CODEBASE_STANDARDS.md         # Maintainability rules
│   ├── DECISIONS.md                  # Architectural decisions and what was rejected
│   ├── demo-script.md
│   ├── adding-a-metric.md
│   └── safety-model.md
├── architecture.svg                  # Request lifecycle and trust boundaries
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── app/
│   │   ├── api/                      # FastAPI routes and Pydantic schemas
│   │   ├── semantic/                 # Catalogue loader, validator, resolver
│   │   ├── intent/                   # LLM call with structured output
│   │   ├── planner/                  # ResolvedRequest to LogicalPlan
│   │   ├── sql/                      # Generator, guard, allowlist, runner
│   │   ├── compose/                  # Result set to summary
│   │   ├── audit/                    # Append-only audit logger
│   │   └── db/                       # Read-only and read-write engines
│   ├── catalogues/
│   │   ├── health-uk/                # v1 ships this only
│   │   ├── motor-uk/                 # documented, not built
│   │   └── property-uk/              # documented, not built
│   ├── seeds/                        # Synthetic data generator
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── golden/                   # Approved Q&A pairs, runs in CI
└── frontend/                         # React + Vite + TypeScript
```

## The catalogue

Vellum-NLQ is multi-catalogue by design. The Python loader supports any number of catalogues mounted under `catalogues/`, with each catalogue scoped to one line of business and one regulatory jurisdiction.

| Catalogue | Status | Notes |
|---|---|---|
| `health-uk` | Shipped in v1 | UK private medical insurance. Fifteen metrics, twelve dimensions. GBP. |
| `motor-uk` | Documented only | Requires bodily injury versus damage split, salvage and subrogation handling, and reserve development as a first-class metric. Largest extension by effort. |
| `property-uk` | Documented only | Requires catastrophe event tagging, building versus contents split, and long-tail claim handling. |

Adding a new catalogue is a YAML and migration exercise. The Python loader, the resolver, the planner, the SQL generator, the guard, the runner, and the API surface do not change.

## The fifteen metrics in health-uk

| Metric | Measures |
|---|---|
| `paid_claims` | Sum of claim payments in the period, by paid date. |
| `incurred_claims` | Paid claims plus change in case reserves, by incurred date. |
| `loss_ratio` | Incurred claims divided by earned premium. |
| `claim_frequency` | Claim count per thousand member months. |
| `claim_severity` | Average paid amount per closed claim. |
| `average_claim_cost` | Mean of net paid amount across non-declined claims. |
| `decline_rate` | Declined claim count divided by adjudicated claim count. |
| `partial_decline_rate` | Claims with at least one declined line divided by adjudicated claims. |
| `turnaround_time` | Median days from claim receipt to adjudication. |
| `reopen_rate` | Claims reopened within ninety days divided by closed claims. |
| `pend_rate` | Claims in pended status divided by total active claims. |
| `duplicate_submission_rate` | Same consultant, same member, same service date, within seven days. |
| `high_value_claim_share` | Share of paid amount from claims over fifty thousand pounds. |
| `network_utilisation` | In-network paid amount divided by total paid amount. |
| `er_visit_rate` | Emergency visits per thousand member months. |

Each one has a YAML file in `backend/catalogues/health-uk/metrics/` with its formula, time anchor, required tables, default filters, synonyms, owner, version, and last-reviewed date.

## Safety model

The guard runs eleven checks on every generated SQL string before execution.

1. Statement type must be SELECT.
2. Exactly one statement per request.
3. Every referenced table on the allowlist.
4. Every referenced column on the allowlist.
5. Every function call on the allowlist.
6. Every join condition matches an edge in `joins.yaml`.
7. Subqueries validated recursively against the same allowlists.
8. LIMIT enforced at ten thousand rows.
9. No `information_schema`, no `pg_catalog`, no other schemas.
10. Comments stripped before parsing.
11. All literals must be bound parameters.

The database role has SELECT only and a fifteen-second `statement_timeout`. The audit log is append-only.

Read `docs/safety-model.md` for the full safety story including the red-team test cases.

## Testing

```bash
make test            # Unit and integration tests
make test-golden     # Golden question set against seeded data
make test-redteam    # Injection attempts the guard must reject
```

The golden test set is in `backend/tests/golden/questions.yaml`. New questions are added by pull request. A change that breaks a golden answer fails CI.

## API

Five endpoints. The contracts are in `backend/app/api/schemas.py`.

| Endpoint | Purpose |
|---|---|
| `POST /ask` | Ask a question. Returns Answer or Clarification. |
| `GET /metrics` | List supported metrics with descriptions, formulas, versions. |
| `GET /dimensions` | List supported grouping and filtering dimensions. |
| `GET /queries/{query_id}` | Audit trace for a past query. |
| `GET /health` | Liveness. Confirms catalogue loaded, database reachable, LLM responsive. |

## What this proves

If you are reading this as a hiring reviewer, the things this repo is meant to demonstrate are:

- I understand that the semantic catalogue is the hard part, not the LLM plumbing.
- I treat safety as a property of the parser and the database role, not a policy in the README.
- I write tests that double as documentation.
- I can ship. The demo runs in two commands. CI is green. The architecture diagram matches the code.
- I chose a domain I can defend in an interview.

## Status

Version 1.0 ships the health-uk catalogue. Motor-uk and property-uk are documented but not built.

## Author

Owura. Founder of Govaxis. Based in London.

## Licence

MIT.
