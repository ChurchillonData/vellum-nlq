# Decisions

This document records the architectural decisions made in Vellum-NLQ, the alternatives that were considered, and why they were rejected. Each entry follows a lightweight ADR pattern. The point of this file is not to be exhaustive. The point is to make the reasoning behind the tricky decisions visible to a reviewer.

If a decision is not listed here, it was either obvious or unimportant.

---

## ADR-001: A semantic catalogue, not a free-form text-to-SQL agent

**Status:** Accepted

**Context.** The default approach in this category is to give the LLM a database schema and let it generate SQL directly. LangChain, LlamaIndex, and most tutorials demonstrate this pattern. It works for demos and fails for regulated analytics, because the model has no way to know that "revenue" in this company means net of refunds and excludes failed payments, while in another company it means gross.

**Decision.** Every metric the system can answer is defined explicitly in a YAML file. The LLM only proposes intent against the catalogue. The catalogue decides whether the system can answer.

**Consequences.**
- The system refuses to answer questions outside the catalogue. This is the intended behaviour, not a limitation.
- Adding a new metric is a YAML edit and a pull request, not a code change.
- The audit trail can name the exact metric definition and version that produced any historical answer.
- The catalogue is the part of the repo that signals domain understanding to a reviewer.

**Rejected alternatives.**
- *Schema-only prompting.* Pass the table definitions to the LLM and let it generate SQL. Rejected because there is no defensible answer when two analysts get different numbers for the same question.
- *Vector retrieval over a SQL examples library.* Embed historical SQL queries and retrieve the closest match. Rejected because retrieval similarity is not the same as semantic correctness, and there is no way to version a query library the way you can version a metric definition.

---

## ADR-002: SQLGlot for AST-level SQL validation

**Status:** Accepted

**Context.** Generated SQL must be validated before execution. Regex-based string matching is not enough because SQL has nested structures, comments, quoting rules, and dialect-specific syntax that regex cannot reliably parse.

**Decision.** Use SQLGlot to parse the generated SQL into an AST, then walk the tree against allowlists for tables, columns, functions, and join conditions.

**Consequences.**
- The guard is a real parser, not a string match. Injection attempts that embed SQL inside string literals, comments, or unicode tricks are rejected because the parser sees them.
- SQLGlot adds a dependency that must be kept in sync with Postgres dialect updates. Acceptable.
- The guard test file is the largest test file in the repo, by design.

**Rejected alternatives.**
- *sqlparse.* Lighter dependency but its parser is less complete and does not handle all Postgres-specific constructs reliably.
- *pg_query (the Postgres parser bindings).* The most accurate parser available but it is a heavier dependency, harder to install on macOS, and overkill for the validation surface this system needs.
- *Regex-based rules.* Considered for thirty seconds and rejected. Regex cannot safely parse SQL.

---

## ADR-003: A read-only database role as a second safety layer

**Status:** Accepted, first slice implemented

**Context.** The SQL guard could be wrong. A new SQLGlot release could introduce a parser bug. The catalogue could contain a typo. The application could be tricked. Defence in depth requires that the database itself refuse to accept anything destructive.

**Decision.** The application connects to Postgres using a role with SELECT privileges only on the application schema, and no privileges on any other schema. The role has a fifteen-second `statement_timeout` and a per-connection `work_mem` cap.

**Current implementation.** The SQL guard and SELECT-only product boundary are
implemented. Product execution still uses local demo data, so the Postgres
read-only role is a target production control.

**Consequences.**
- If the guard ever lets a destructive statement through, the database rejects it with a permissions error.
- Migrations run as a separate role, never the application role.
- The seed script runs as a third role, used only at setup time.

**Rejected alternatives.**
- *Trust the guard.* The guard is one piece of code maintained by one person. The database role is an additional independent boundary at almost zero cost.
- *Row-level security only.* RLS is useful for multi-tenancy, which is out of scope for v1. It does not replace the read-only constraint.

---

## ADR-004: Pydantic models for the catalogue, validated at startup

**Status:** Accepted

**Context.** The catalogue is YAML. YAML is permissive. A typo in a metric definition that names a non-existent column would not be caught until the metric was requested, possibly long after the typo was introduced.

**Decision.** Every YAML file is loaded into a typed Pydantic model at application startup. The loader validates cross-references (every required table exists, every formula column exists, every synonym is unique, every join references real tables). Startup fails loudly if the catalogue is inconsistent.

**Consequences.**
- A broken catalogue cannot be deployed. The container fails to start.
- The catalogue test file exercises the validator extensively.
- The cost is paid once per restart. Negligible.

**Rejected alternatives.**
- *Validate on first use.* Defers the failure to runtime. Worse user experience and harder to debug.
- *Trust the YAML.* Not an option. Catalogue typos are the most common kind of catalogue change.

---

## ADR-005: SQLAlchemy Core, not the ORM, for query construction

**Status:** Accepted

**Context.** The SQL generator needs to produce parameterised queries from a logical plan. The options were the SQLAlchemy ORM, SQLAlchemy Core, raw string concatenation, and a custom AST builder.

**Decision.** SQLAlchemy Core. The generator builds queries by composing expression objects, which produces parameterised SQL when compiled.

**Consequences.**
- The system never builds SQL by string concatenation. This removes a class of injection bugs by construction.
- The Core expression API is verbose but explicit. Reviewers can trace exactly how a generated SQL string was assembled.
- No ORM means no lazy loading, no session management overhead, no surprises.

**Rejected alternatives.**
- *SQLAlchemy ORM.* Overkill for a read-only application. The ORM is designed for object lifecycle management, which this system does not have.
- *Raw string concatenation with parameter binding.* Possible but error-prone. SQLAlchemy Core provides the same control with safer ergonomics.
- *A custom SQL AST builder.* Reinvents the wheel.

---

## ADR-006: OpenAI as the LLM provider, behind a provider adapter

**Status:** Accepted, first production slice implemented

**Context.** The intent interpreter calls an LLM with structured output. Vellum-NLQ needs the model to propose typed analytics intent while the catalogue and deterministic planner remain the authority for what can execute.

**Decision.** Use the OpenAI API as the configured provider and use structured outputs for intent extraction. Wrap the call behind an `IntentProvider` protocol so swapping providers later is a contained change.

**Current implementation.** The backend uses a deterministic provider by
default, has a fake provider for tests, and includes an OpenAI provider behind
`VELLUM_INTENT_PROVIDER=openai`. The provider returns structured intent only.
It cannot return SQL through the intent schema, and provider output still passes
through catalogue resolution, deterministic planning, SQL guard validation,
execution, and audit. OpenAI output is sanitized against the active catalogue,
low-confidence proposals are discarded, and provider failures fall back to
deterministic parsing by default.

**Consequences.**
- The intent interpreter has one source of LLM-specific code, in `app/intent/openai_provider.py`.
- Tests use a `FakeIntentProvider` that returns canned `IntentResult` objects. No LLM is called in unit tests.
- The CI path stays deterministic because unit and core integration tests never require a live OpenAI call.

**Rejected alternatives.**
- *Anthropic as the default.* Also viable, but rejected for this build because the implementation owner is using an OpenAI API key and OpenAI structured outputs fit the typed intent boundary.
- *Open-source local models.* Llama-class models can do structured output via grammar-constrained sampling. Rejected for v1 because the operational overhead is not worth it for a portfolio project. Documented as a future option.

---

## ADR-007: Postgres only, not SQLite or DuckDB

**Status:** Accepted, target

**Context.** Tests run against a real database. The choice was Postgres in Docker, SQLite for tests with Postgres in production, or DuckDB.

**Decision.** Postgres for both tests and production. The test container is started by docker-compose and torn down on completion.

**Current implementation.** Deterministic demo execution still defaults to
in-memory SQLite so the backend runs without Docker. A guarded Postgres
execution path is available behind `VELLUM_EXECUTION_BACKEND=postgres` and uses
the read-only database URL. Live Postgres integration tests are implemented as
an optional suite because they require a migrated and seeded database.

**Consequences.**
- The test suite needs Docker to run. CI uses the github-actions Docker runner.
- The SQL generator does not need a dialect switch because there is only one dialect.
- Real Postgres features (window functions, generated columns, `LATERAL`) work in tests.

**Rejected alternatives.**
- *SQLite for tests, Postgres in production.* Standard advice. Rejected because the SQL dialect differences are exactly the kind of thing the SQL guard needs to handle correctly, and tests must exercise the real path.
- *DuckDB.* Interesting for analytical workloads but rejected because the catalogue assumes Postgres-style date functions and reserve snapshots, and DuckDB's concurrency model is not what production claims systems use.

---

## ADR-008: A clarification response is a first-class type, not an error

**Status:** Accepted

**Context.** When the system cannot answer a question, the options are to return an error, to return a best-guess answer with a low-confidence flag, or to return a structured clarification request.

**Decision.** The `/ask` endpoint returns either an `Answer` or a `Clarification`. Both are valid 200 responses. The frontend renders them differently.

**Consequences.**
- Clarifications are a normal part of the request lifecycle, not exceptional.
- The audit log records clarifications the same way it records answers.
- Reviewers see the clarification path on the demo, which is one of the things that makes this project different.

**Rejected alternatives.**
- *Return an error.* Wrong shape. The user did nothing wrong. The system just needs more information.
- *Best-guess answer with a flag.* This is the failure mode of most demos. Rejected because the cost of a confident wrong answer in claims analytics is much higher than the cost of asking a follow-up.

---

## ADR-009: Multi-catalogue from day one, even though only one ships

**Status:** Accepted

**Context.** Version one only ships the health-uk catalogue. The natural temptation is to hard-code the catalogue path and refactor later. The cost of doing it right now is small. The cost of refactoring later is high.

**Decision.** The catalogue loader supports multiple catalogues from day one. The `motor-uk` and `property-uk` directories exist as placeholders with README files describing what each would require. The configuration names the active catalogue. The architecture does not assume there is only one.

**Consequences.**
- The directory tree visibly signals the multi-catalogue intent to any reviewer.
- The Python loader is slightly more complex but the complexity is paid once.
- Adding motor-uk in version two is a YAML and migration exercise, not a refactor.

**Rejected alternatives.**
- *Hard-code health-uk and refactor later.* Rejected because the refactor would touch the catalogue loader, the resolver, the API, the audit log, and the tests. Doing it once now is far cheaper.

---

## ADR-010: Synthetic seed data, not real claims data

**Status:** Accepted, target scale

**Context.** Real claims data is regulated and cannot be shipped in a public repo. The choice was synthetic data, anonymised real data, or no seed data.

**Decision.** A synthetic data generator that produces realistic UK PMI claims for two hundred thousand members across eighteen months. Distributions are calibrated to public ABI and PRA aggregate statistics for the UK PMI market.

**Current implementation.** The generator supports both the smaller local
development slice and a portfolio profile of 200,000 members across 18 months.
The portfolio path loads in chunks and has a dry-run report for table-level row
counts. Full performance tuning against a seeded database is still planned.

**Consequences.**
- The repo is self-contained. Anyone can clone and run.
- The data is fictional but realistic enough that aggregate metrics produce plausible numbers (loss ratios in the 0.78 to 0.92 range, decline rates around 5 to 8 per cent, average claim costs in the expected band).
- The seed script is itself a small project that demonstrates statistical fluency.

**Rejected alternatives.**
- *Anonymised real data.* No legal route to publish, even anonymised. Rejected immediately.
- *Public synthetic datasets.* The available public datasets (CMS Synpuf, MIMIC) are US healthcare, not UK PMI. Wrong domain.
- *No seed data, bring your own.* Defeats the point of a portfolio project that should run for any reviewer in two commands.

---

## ADR-011: A golden test set in YAML, run on every commit

**Status:** Accepted

**Context.** Unit tests cover individual modules. They do not catch a regression where the system as a whole gives a different answer to a known question. Snapshot testing of LLM output is unreliable because models change.

**Decision.** A YAML file of approved question-and-answer pairs. The golden suite runs every question through the product `/ask` endpoint. The test asserts on the type of response, the metric used, grouped dimensions when present, row shape, and safety or scope reasons.

**Current implementation.** The first YAML golden suite lives at
`backend/tests/golden/questions.yaml` and is executed by
`backend/tests/golden/test_golden_questions.py`. It covers answer,
date-range-required, clarification, blocked, and out-of-scope states.

**Consequences.**
- A change that breaks a golden answer fails the build.
- New questions are added by opening a pull request that includes the expected behaviour.
- The golden file doubles as documentation. A reviewer reading it learns what the system does and refuses.

**Rejected alternatives.**
- *Snapshot tests of LLM output.* Brittle. A model upgrade breaks every test.
- *No integration tests.* Defeats the point of building a system instead of a collection of parts.

---

## ADR-012: The frontend is small but real

**Status:** Accepted, first demo slice implemented

**Context.** The temptation in a backend-heavy project is to skip the frontend or use a Streamlit demo. The audience for this repo includes hiring reviewers who will spend ninety seconds clicking around before reading any code.

**Decision.** A small React + Vite + TypeScript app. The Ask workspace renders answer, clarification, blocked, date-range-required, and out-of-scope states. The transparency panel shows SQL, metric definition, validation, and audit IDs. Catalogue and Audit pages stay real but bounded.

**Current implementation.** Frontend mockups are stored under
`design-mockups/frontend`. The React app is scaffolded and wired to `/ask`,
`/ask/examples`, `/metrics`, `/queries/{query_id}`, and `/health`, with saved
demo fallbacks when the API is unavailable.

**Consequences.**
- Reviewers see the transparency panel without being asked to look for it.
- The frontend is bounded enough to ship in four days as part of week three.
- The repo demonstrates frontend competence without claiming to be a frontend project.

**Rejected alternatives.**
- *Streamlit.* Fine for internal demos. Wrong signal for a portfolio project that wants to read as engineered software.
- *No frontend, just the API.* Reviewers will not call the API. The demo video would not exist.

---

## ADR-013: Partner mappings are validated before runtime rewrite

**Status:** Accepted, first validation slice implemented

**Context.** A real insurer will not have tables named exactly like Vellum's
canonical `health-uk` catalogue. The risky version of this problem is to start
rewriting generated SQL against arbitrary partner table names before we know
whether the source schema actually contains the fields needed by the governed
metrics.

**Decision.** Partner schema mapping starts as a typed YAML validation layer.
The mapping must point canonical Vellum tables and columns to partner source
tables and columns. Vellum validates the canonical side and reports coverage.
Runtime SQL rewriting is a later step after a private partner schema inventory
is available.

**Consequences.**
- A partner engineering team can review the exact fields Vellum needs without
  exposing real data.
- Unknown canonical tables or columns fail fast.
- Mapping gaps become explicit onboarding work rather than hidden SQL failures.
- The public repository can include a fictional mapping template safely.

**Rejected alternatives.**
- *Rewrite SQL immediately.* Rejected because it gives a false sense of pilot
  readiness before source fields and transforms have been confirmed.
- *Ask partners to rename their warehouse tables.* Rejected because real
  insurers will not reshape production data just to test a portfolio demo.

---

## What is deliberately not in this document

These are decisions a reviewer might expect to see explained, but the reasoning is obvious or generic.

- *Python over Go or Rust.* The LLM and Pydantic ecosystems are in Python.
- *FastAPI over Flask or Django.* FastAPI is the default for Python APIs in 2026, and its Pydantic integration matters for this project.
- *Docker Compose for local dev.* Standard.
- *GitHub Actions for CI.* Standard.
- *Pytest for tests.* Standard.

If any of these become non-obvious later, they get their own ADR.

---

## Open questions

These are decisions I have not yet made and would like reviewer input on.

1. *Streaming responses.* The current API is synchronous. For long queries, streaming the SQL first, then the result, then the summary would be a better user experience. Held back because it complicates the audit log.
2. *Caching.* Result caching keyed on query hash with TTL based on the underlying table's last write time would improve latency for repeated questions. Held back because the invalidation logic is more complex than it sounds.
3. *Multi-currency.* The health-uk catalogue is GBP only. If motor-uk and property-uk are added and a carrier writes business across the UK and Ireland, the catalogue needs a currency dimension. Not built. Probably needs an ADR of its own.

---

*Last updated: 2026-05-21*
