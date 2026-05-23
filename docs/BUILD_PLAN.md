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
- `GET /ask/examples` exposes seventeen golden demo questions, and tests run each
  example through `/ask` to protect answer, date-range-required,
  clarification, blocked, and out-of-scope states.
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
- `decline_rate` now has an ungrouped deterministic path through catalogue
  resolution, planning, guarded SQL generation, local demo execution, and ask
  examples. Grouping by consultant specialty is the next slice.
- `decline_rate by consultant specialty` is now supported as the first grouped
  analytics path, using `providers.specialty` through the approved
  `claim_lines -> providers` join.
- `backend/tests/golden/questions.yaml` now defines the first YAML golden
  question contract, and `make test-golden` runs it through `/ask`.
- `incurred_claims` and `claim_severity` are now executable deterministic
  metrics through catalogue resolution, planning, guarded SQL generation, local
  demo execution, ask examples, and golden questions.

Current backend gaps before calling this phase complete:

- Natural-language parsing is intentionally narrow: quarter phrases, ISO date
  ranges, and plan tiers are supported; richer date language is still planned.
- Grouped analytics are currently limited to `decline_rate` by
  `consultant_specialty`; broader dimension support is still planned.
- Additional grouped metrics and dimensions beyond consultant specialty are
  still planned.

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
- Every `POST /ask` outcome now writes a local JSONL audit event with a query
  ID, including answer, clarification, blocked, date-range-required, and
  out-of-scope states.
- `GET /queries/{query_id}` can read back local JSONL audit events while the
  Postgres audit table is not built yet.
- `backend/tests/redteam/` now contains the first red-team slice. It checks
  destructive user intent through `/ask` and unsafe generated-SQL shapes through
  the SQL guard. `make test-redteam` runs this suite.
- The SQL guard now rejects embedded string/date literals and uncontrolled
  grouped result sets. Grouped generated SQL must carry an approved result
  limit, currently capped at 50 rows.

Current safety and audit gaps:

- Product execution is not using a Postgres read-only role yet.
- The Postgres append-only audit table is not built yet.
- Red-team coverage is still a first slice; broader prompt-injection and
  obfuscation cases are planned.
- Broader result-size policies for future dimensions are planned as grouped
  analytics expands.

## Phase 4: OpenAI Intent Layer

Status: in progress

- Use the OpenAI API for structured intent extraction.
- Keep provider code behind a narrow interface and use fakes in tests.
- Return clarifications for ambiguous and out-of-scope questions.

Current first slice:

- `IntentProvider` now separates natural-language intent extraction from SQL
  generation.
- The default deterministic provider preserves the current parser behaviour.
- The OpenAI provider is available behind `VELLUM_INTENT_PROVIDER=openai` and
  returns structured intent only: metric, date range, plan tier, grouping, and
  confidence.
- Unit tests use a fake provider to prove provider output still flows through
  catalogue resolution, deterministic planning, SQL guard validation, local demo
  execution, and audit.
- Unsafe user intent is still blocked before provider metric intent can run.

Current gaps:

- No live OpenAI integration test is run in CI.
- Provider fallback and retry policy are intentionally minimal.
- The structured intent schema is narrow and covers only the current demo
  fields.

## Phase 5: Frontend And Demo

- Build the analyst-facing query UI.
- Show metric provenance, SQL, joins, validation state, and audit IDs.
- Scale the synthetic seed data from the small development slice to the
  portfolio demo target of 200,000 members across 18 months.
- Review the synthetic distributions so loss ratio, frequency, severity, and
  decline metrics look plausible in the demo dataset.
- Expand golden questions, demo data polish, and reviewer-friendly
  documentation.
