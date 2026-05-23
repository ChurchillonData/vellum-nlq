# Build Plan

Vellum-NLQ is being built as a portfolio-quality system in phases. The overview
documents describe the target product. This plan keeps the implementation path
honest while the code catches up with that target.

## Phase 1: Foundation

Status: in progress

- Establish the repository layout and backend package.
- Add the Postgres schema, first migration, and local database container setup.
- Add deterministic synthetic seed data for the first development slice.
- Add the first `health-uk` semantic catalogue slice.
- Validate catalogue structure and cross-references at load time.
- Expose a minimal backend health endpoint.
- Keep the OpenAI provider boundary visible in configuration without calling an
  LLM yet.

Exit criteria:

- `backend` unit tests pass.
- Alembic can render the first migration SQL.
- The first metric definition loads from YAML.
- The backend can report that it is alive and name the active catalogue.

## Phase 2: Deterministic Analytics Path

Status: in progress

- Resolve a small set of catalogue-backed analytics requests without an LLM.
- Build logical plans and parameterised SQL for the first metrics.
- Return SQL provenance alongside query results.

Current first slice:

- Structured `loss_ratio` request resolves through the catalogue into a logical
  plan, parameterised SQL, and provenance without database execution.
- A development preview endpoint exposes that structured request path until the
  final `/ask` flow is ready.
- `GET /metrics` returns active catalogue metric definitions for the future
  Catalogue Explorer frontend.
- `POST /queries/execute` runs the guarded `loss_ratio` path against an
  in-memory synthetic demo dataset and returns result rows, an answer summary,
  SQL, parameters, validation, and provenance.
- `POST /queries/resolve` deterministically maps simple questions to catalogue
  metrics or returns clarification candidates without calling an LLM.
- The resolve path blocks destructive database intent before planning or SQL
  generation, returning a safety rule ID for the UI rejection state.
- `POST /ask` now orchestrates the first product-facing flow: answer,
  clarification, or blocked state from one endpoint.
- `GET /ask/examples` exposes twelve golden demo questions, and tests run each
  example through `/ask` to protect answer, clarification, and blocked states.
- `docs/api-contract.md` documents the current backend API surface for frontend
  integration and reviewer walkthroughs.
- `paid_claims` now has a deterministic catalogue-backed path through
  resolution, planning, SQL generation, guard validation, demo execution, and
  golden ask examples.
- The ask flow now returns `out_of_scope` for forecasting and prediction
  questions, matching the canonical demo script's forecast refusal state.
- `claim_frequency` now completes the first executable clarification trio:
  `loss_ratio`, `paid_claims`, and `claim_frequency`.
- `POST /ask` now infers supported date ranges and plan-tier filters from the
  question for the product endpoint. It handles quarter phrases such as
  `Q1 2026`, ISO date ranges, and the current demo plan tiers without OpenAI.

Current backend gaps before calling this phase complete:

- Natural-language parsing is intentionally narrow: quarter phrases, ISO date
  ranges, and plan tiers are supported; richer date language is still planned.
- Grouped and dimensioned analytics are not implemented yet.
- Catalogue metrics `incurred_claims` and `claim_severity` are defined but not
  executable yet.
- The canonical demo's `decline_rate by consultant specialty` question is not
  supported yet because `decline_rate` and grouping are future work.

## Phase 3: Safety And Audit

Status: in progress

- Add the SQL guard and allowlists.
- Run queries through a read-only database role.
- Add the append-only audit path and red-team tests.

Current first slice:

- SQLGlot parses generated SQL before execution exists.
- The first guard rules reject comments, parse failures, stacked statements,
  non-SELECT statements, and system schema references.
- The guard now checks physical tables, columns, functions, and joins against
  the active semantic catalogue for the generated `loss_ratio` path.
- User questions with destructive database intent are blocked before SQL
  planning, while generated SQL is still guarded before execution.
- Successful preview requests now create a local JSONL audit event with a
  query ID, SQL, parameters, request payload, and validation outcome.
- Successful local demo executions now write audit events with execution mode,
  row count, and answer summary.
- `GET /queries/{query_id}` can read back local JSONL audit events while the
  Postgres audit table is not built yet.

Current safety and audit gaps:

- Product execution is not using a Postgres read-only role yet.
- The Postgres append-only audit table is not built yet.
- The full red-team test suite is not built yet.
- Guard-level result-size caps and literal-parameter enforcement are planned
  but not implemented yet.

## Phase 4: OpenAI Intent Layer

- Use the OpenAI API for structured intent extraction.
- Keep provider code behind a narrow interface and use fakes in tests.
- Return clarifications for ambiguous and out-of-scope questions.

## Phase 5: Frontend And Demo

- Build the analyst-facing query UI.
- Show metric provenance, SQL, joins, validation state, and audit IDs.
- Scale the synthetic seed data from the small development slice to the
  portfolio demo target of 200,000 members across 18 months.
- Review the synthetic distributions so loss ratio, frequency, severity, and
  decline metrics look plausible in the demo dataset.
- Add golden questions, demo data polish, and reviewer-friendly documentation.
