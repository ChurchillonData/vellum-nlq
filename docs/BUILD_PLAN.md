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
- Successful preview requests now create a local JSONL audit event with a
  query ID, SQL, parameters, request payload, and validation outcome.
- Successful local demo executions now write audit events with execution mode,
  row count, and answer summary.
- `GET /queries/{query_id}` can read back local JSONL audit events while the
  Postgres audit table is not built yet.

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
