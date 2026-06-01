# Build Plan

Vellum-NLQ is being built as a portfolio-quality system in phases. The overview
documents describe the target product. This plan keeps the implementation path
honest while the code catches up with that target.

## Phase 1: Foundation

Status: complete for local development

- Establish the repository layout and backend package.
- Add the Postgres schema, first migration, and local database container setup.
- Add deterministic synthetic seed data for the first development slice.
- Add the first `health-uk` semantic catalogue slice.
- Validate catalogue structure and cross-references at load time.
- Expose a minimal backend health endpoint.
- Keep the OpenAI provider boundary visible in configuration without calling an
  LLM yet.

Current foundation:

- `docker-compose.yml` starts a local Postgres 16 database.
- Local roles are separated into `vellum_admin`, `vellum_seeder`, and
  `vellum_readonly`; the audit slice also adds `vellum_auditor`.
- Alembic migration `0001` creates the first claims analytics schema, indexes,
  and local role grants.
- `backend/seeds/generate.py` loads deterministic synthetic data through the
  seeder role.
- `make seed` starts Postgres, runs migrations, loads data, and validates the
  catalogue.
- `docs/local-postgres.md` documents the local database workflow.

Exit criteria:

- `backend` unit tests pass.
- Alembic can run the first migration.
- The first metric definition loads from YAML.
- The backend can report that it is alive and name the active catalogue.

## Phase 2: Deterministic Analytics Path

Status: complete for backend v1 demo

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
- `GET /ask/examples` exposes twenty golden demo questions, and tests run each
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
- `decline_rate` has deterministic ungrouped and consultant-specialty grouped
  paths through catalogue resolution, planning, guarded SQL generation, local
  demo execution, and ask examples.
- `decline_rate by consultant specialty` is now supported as the first grouped
  analytics path, using `providers.specialty` through the approved
  `claim_lines -> providers` join.
- `backend/tests/golden/questions.yaml` now defines the first YAML golden
  question contract, and `make test-golden` runs it through `/ask`.
- `incurred_claims` and `claim_severity` are now executable deterministic
  metrics through catalogue resolution, planning, guarded SQL generation, local
  demo execution, ask examples, and golden questions.
- Backend-v1 natural-language parsing covers quarter phrases, ISO date ranges,
  `last month`, `last six months`, year-to-date, full-year phrases, demo plan
  tiers, and supported grouping phrases.
- Common grouped demo outputs now support `plan_tier` and `region` across the
  supported metrics, with guarded 50-row limits.
- `decline_rate by consultant_specialty` remains the consultant-join grouped
  path for the demo.

## Phase 3: Safety And Audit

Status: complete for backend v1 demo

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
  default audit backend is JSONL.
- `backend/tests/redteam/` checks destructive user intent, delete-like synonyms,
  prompt-injection-style destructive requests, and unsafe generated-SQL shapes
  through the SQL guard. `make test-redteam` runs this suite.
- The SQL guard now rejects embedded string/date literals and uncontrolled
  grouped result sets. Grouped generated SQL must carry an approved result
  limit, currently capped at 50 rows.
- `VELLUM_AUDIT_BACKEND=postgres` stores audit events in the append-only
  `audit_events` table through the `vellum_auditor` role.
- Alembic migration `0002` creates the audit table, audit indexes, and
  SELECT/INSERT-only local audit grants.

Remaining production hardening:

- Broader result-size policies for future dimensions are planned as grouped
  analytics expands.
- Live Postgres integration tests and operational security review are still
  production-readiness work.

## Phase 3B: Postgres Execution Path

Status: complete for first backend slice

- `VELLUM_EXECUTION_BACKEND` selects the execution backend.
- `local_demo` remains the default so the project runs without Docker.
- `postgres` executes guarded generated SQL through
  `VELLUM_READONLY_DATABASE_URL`.
- The Postgres executor refuses SQL that failed guard validation.
- The Postgres executor uses SQLAlchemy `text(...)` with bound parameters from
  the generator; it does not accept user-written SQL.
- API execution responses and audit events now surface the actual execution
  mode.
- Unit tests cover read-only URL selection, parameter passing, row caps, and API
  response/audit mode.

Current gaps:

- Live Postgres integration tests are not implemented yet because Docker is not
  available in the current execution environment.

## Phase 4: OpenAI Intent Layer

Status: complete for backend v1 demo

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
- OpenAI provider output is sanitized against the active catalogue. Unknown
  metrics, unknown plan tiers, and unsupported groupings are discarded before
  resolution.
- Low-confidence OpenAI proposals are discarded so the request falls back into
  the normal deterministic parsing and clarification path.
- The OpenAI client has configured timeout and retry settings, and provider
  failures fall back to deterministic parsing by default.
- Unit tests use a fake provider to prove provider output still flows through
  catalogue resolution, deterministic planning, SQL guard validation, local demo
  execution, and audit.
- Unsafe user intent is still blocked before provider metric intent can run.

Remaining production hardening:

- No live OpenAI integration test is run in CI.
- The structured intent schema is narrow and covers only the current demo
  fields.

## Phase 5: Frontend And Demo

Status: in progress

- Build the analyst-facing query UI.
- Show metric provenance, SQL, joins, validation state, and audit IDs.
- Run implemented backend and frontend checks in GitHub Actions on every push
  and pull request.
- Scale the synthetic seed data from the small development slice to the
  portfolio demo target of 200,000 members across 18 months.
- Review the synthetic distributions so loss ratio, frequency, severity, and
  decline metrics look plausible in the demo dataset.
- Expand golden questions, demo data polish, and reviewer-friendly
  documentation.

Current frontend slice:

- The React Ask workspace calls the real `/ask` endpoint and renders answer,
  clarification, blocked, out-of-scope, and date-range-required states.
- Demo question controls load from `/ask/examples` when the backend is
  available, with saved demo fallbacks for no-API local viewing.
- Saved frontend demo fallbacks now mirror the twenty backend ask examples and
  all six active catalogue metrics, so offline viewing still shows the same
  answer, clarification, blocked, date-required, and out-of-scope states.
- Clarification candidates can be selected in the UI; the selected
  `metric_id` is sent back to `/ask` and still goes through catalogue
  resolution, deterministic planning, SQL guard validation, execution, and
  audit.
- The Audit view can inspect the latest query ID or a pasted query ID through
  `GET /queries/{query_id}` and render request, resolution, SQL, validation,
  provenance, safety/scope notes, and execution summary.
- The Catalogue Explorer now consumes the richer `/metrics` payload for all
  active metrics, including catalogue-owned formulas, versions, owners,
  allowed dimensions, join previews, synonyms, and review dates.
- The top-bar catalogue and operational badges now read `/health`, so the
  frontend shows the active catalogue and backend availability instead of a
  hardcoded status.
- The synthetic seed loader now supports a portfolio profile of 200,000 members
  across 18 months, loaded in chunks so large demo preparation does not require
  building the full dataset in memory at once.
- A `make db-check` readiness command validates admin, seeder, read-only, and
  audit Postgres role connections before local or portfolio seeding begins.
- A local-only `make db-reset-local` workflow can recreate the Docker Postgres
  volume, rerun migrations, and verify role credentials when a stale local
  volume causes password mismatches.
- A `make postgres-smoke` command verifies seeded Postgres table counts and
  representative guarded query execution through the read-only role.
- GitHub Actions CI now runs backend unit tests, golden question tests,
  red-team tests, and the frontend production build.
