# Adding a Metric

This document is the runbook for adding a new metric to a Vellum-NLQ catalogue. It exists because adding a metric is the most common change to this system, and the wrong way to do it is to copy an existing YAML file, edit the formula, and hope. The right way is documented here.

If you are adding a dimension instead of a metric, see `adding-a-dimension.md`. If you are adding a whole new catalogue (motor-uk, property-uk), see `adding-a-catalogue.md`.

## When to add a metric

Before you write any YAML, answer these four questions honestly.

1. **Is this a real metric that the business uses, or is it a one-off question someone asked?** Metrics are durable. Questions are not. If the same calculation appears in three different conversations across two teams, it is a metric. If one person asked it once, it is a query.

2. **Who owns the definition?** Every metric in the catalogue has an owner field. The owner is the team or role that gets called when the definition needs to change. Actuarial owns loss ratio. Claims operations owns turnaround time. If no team will own this metric, do not add it.

3. **Can you write the formula in one line?** If the formula needs three paragraphs of caveats, you have not finished thinking about it. Go back and define the conditions under which the metric is defined, then write the formula for that case.

4. **Does the data exist to compute it?** Check `catalogues/health-uk/tables.yaml` for the required columns. If the data is not in the schema, adding a metric is the second step. The first step is a migration.

If you answered yes to all four, proceed.

## The ten steps

Each step has a checkpoint. If a checkpoint fails, stop and fix it before moving on.

### 1. Draft the YAML

Create `catalogues/health-uk/metrics/<metric_id>.yaml`. Use kebab-case for filenames, snake_case for the metric ID inside.

```yaml
id: <metric_id>
label: <Human-readable name>
description: |
  Two to four sentences. State what the metric measures, which dates anchor
  it, and any default exclusions. Be precise enough that a regulator could
  read it and understand exactly what is being computed.
formula:
  numerator: "SUM(...)"
  denominator: "SUM(...) "    # omit for non-ratio metrics
  expression: "..."
required_tables:
  - <table_a>
  - <table_b>
time_anchor: <table>.<date_column>
currency: GBP                  # omit if dimensionless (rates, counts)
filters_default:
  - "<sql predicate>"
synonyms:
  - <natural variant 1>
  - <natural variant 2>
owner: <team>                  # actuarial, claims, finance, fraud
version: 0.1.0
last_reviewed: <YYYY-MM-DD>
```

Use version `0.1.0` for a new metric. Increment to `1.0.0` when the metric ships in a tagged release.

**Checkpoint.** The file is valid YAML and every field is present. Run `make validate-catalogue` to confirm.

### 2. Check the tables and columns are on the allowlist

Open `catalogues/health-uk/tables.yaml`. Every table named in `required_tables` must be there. Every column referenced in `numerator`, `denominator`, `expression`, and `filters_default` must be in the columns list of its table.

If a column is missing, you have two choices. Either you are using the wrong column name (look at the migration files) or the column genuinely is not in the schema and you need a migration first. Do not edit `tables.yaml` to add a column that is not in the database.

**Checkpoint.** `make validate-catalogue` reports no missing references.

### 3. Check the join graph

If the metric requires data from two or more tables, open `catalogues/health-uk/joins.yaml`. The join path from the first table to each other table must exist as a chain of edges in the graph.

For example, a metric that joins `claims` to `premium` requires either a direct edge or a path through `members`. If the path does not exist, you have three choices.

- Add the edge to `joins.yaml`, if the join is genuinely valid and you can document the cardinality.
- Rethink the metric to use a different table that is already reachable.
- Push back on the metric definition because the join would be misleading.

Do not add an edge to `joins.yaml` casually. Every edge expands the set of queries the system can generate, including ones nobody asked for. Adding edges is a meaningful design change.

**Checkpoint.** Every join the metric needs is reachable through `joins.yaml`.

### 4. Add synonyms

The synonyms list is how the intent interpreter maps natural-language phrases to your metric. For a metric called `decline_rate`, useful synonyms include "decline ratio", "claim decline rate", "claims declined", and any internal jargon the team uses ("DR", "denials" if the team still says that).

Avoid synonyms that collide with other metrics. If `claim_severity` and `average_claim_cost` both have "average claim" as a synonym, the resolver cannot tell which the user wanted. The resolver will return a clarification, which is correct, but you have created an avoidable clarification.

**Checkpoint.** Run `make check-synonyms`. It fails if any synonym appears in two metrics.

### 5. Add demo examples and golden coverage

Current build: open `backend/app/ask/examples.py` and add examples when the
metric is executable through `/ask`.

Then open `backend/tests/golden/questions.yaml` and add the same contract
coverage there.

Add at least three new entries across the current examples and golden suite.

- One question that should answer using the new metric.
- One question that should return a clarification because the new metric is ambiguous against an existing one.
- One question that should be rejected as out of scope, if applicable.

Example for a new metric called `pend_rate`:

```yaml
- id: g0XX
  question: "What is the pend rate this month?"
  expects:
    type: answer
    metric_id: pend_rate
    dimensions: [reporting_month]
    row_count: 1
    approximate_value: 0.04
    tolerance: 0.01

- id: g0XY
  question: "How many claims are stuck?"
  expects:
    type: clarification
    reason: ambiguous_metric
```

The `approximate_value` is the value you expect when the test runs against the seeded data. The tolerance accounts for synthetic-data variance.

**Checkpoint.** `make test-unit` passes, including the `/ask` examples test.
`make test-golden` also passes. If a metric answer fails, either the formula is
wrong or the expected value is wrong. Both are useful failures.

### 6. Add unit tests for the resolver

Open `backend/tests/unit/test_resolver.py`. Add tests that exercise the new metric specifically.

```python
def test_resolver_finds_new_metric():
    request = AnalyticsRequest(metric="pend_rate", dimensions=["reporting_month"])
    resolved = resolver.resolve(request)
    assert resolved.metric_id == "pend_rate"
    assert resolved.time_anchor == "claims.received_date"
```

```python
def test_resolver_handles_synonym():
    request = AnalyticsRequest(metric="pended claims rate", dimensions=[])
    resolved = resolver.resolve(request)
    assert resolved.metric_id == "pend_rate"
```

**Checkpoint.** `make test` passes.

### 7. Snapshot the generated SQL

Open `backend/tests/unit/test_generator.py`. Add a snapshot test that freezes the SQL the generator produces for a canonical query against the new metric. Snapshot tests catch regressions where a refactor accidentally changes the generated SQL.

```python
def test_generated_sql_for_pend_rate(snapshot):
    plan = build_logical_plan(metric="pend_rate", dimensions=["reporting_month"])
    sql = generator.generate(plan)
    snapshot.assert_match(sql, "pend_rate_by_month.sql")
```

The first run creates the snapshot. Subsequent runs compare against it. If the SQL legitimately needs to change, update the snapshot with `pytest --snapshot-update`.

**Checkpoint.** `make test` passes and the snapshot file exists in `backend/tests/unit/snapshots/`.

### 8. Add the metric to the safety red-team set

Open `backend/tests/unit/test_guard.py`. Confirm the new metric does not introduce any column or join references that the guard would reject. If it does, you have either a bug in the metric definition or a bug in the allowlist. Fix the right one.

If the new metric requires a function call that is not on the function allowlist (for example, `PERCENTILE_CONT` for a median calculation), update `backend/app/sql/allowlist.py` to add that function, and add a unit test that proves the guard accepts it and another that proves it still rejects unsafe functions.

**Checkpoint.** `make test-guard` passes.

### 9. Update the README metrics table

Open `README.md` and add a row to the metrics table. Keep the description to one sentence in the same style as the existing rows. If the table is getting long (over twenty metrics), break it into sub-tables grouped by metric family.

**Checkpoint.** Visual review. The table renders correctly on GitHub.

### 10. Open the pull request

The PR description must include:

- The metric ID and label.
- The owner team.
- The question that motivated adding it (one sentence).
- A screenshot of the system answering a question that uses the metric.
- The output of `make test-golden` showing the new entries pass.

The PR is reviewed by the catalogue owner team named in the YAML `owner` field. If you are the owner, the PR is reviewed by one other engineer.

**Checkpoint.** PR merged. `last_reviewed` field in the YAML updated to the merge date.

## Common mistakes

### Defining a metric that is actually two metrics

If you find yourself writing "this metric includes X unless Y, in which case it excludes Z," you probably have two metrics. Split them. `paid_claims` and `paid_claims_excluding_capitation` are two metrics, not one with a conditional.

### Using the wrong date anchor

Loss ratio uses `incurred_date` because the actuaries need to see claims allocated to the period in which the risk was incurred. Turnaround time uses `received_date` because the operations team measures from when the claim arrived. Using the wrong anchor produces a number that looks right and is not.

If you are unsure which anchor to use, ask the owner team. Do not guess.

### Adding a synonym that is also a dimension

If your metric has the synonym "by month", you are not adding a synonym, you are adding a grouping. Synonyms describe the metric. Groupings are dimensions. Keep them separate.

### Skipping the snapshot test

The snapshot test for the generated SQL is the only thing that catches a class of refactor bugs where the generator silently changes the SQL it emits. Skipping it makes the system harder to maintain later.

### Forgetting to bump the version

If you change an existing metric's formula, bump the version. The audit log records which version produced each historical answer, and that trail breaks if two different formulas share a version number.

## What good looks like

A well-added metric has these properties.

- The YAML file is under fifty lines.
- The description reads like a regulatory definition, not a marketing tagline.
- The synonyms cover the three or four ways someone in the business would actually phrase the question.
- The golden test set includes both happy-path and clarification cases.
- The PR description includes the screenshot.
- The owner team approved the merge.

That is the standard. Anything less, send it back.
