# Partner Schema Mapping

Vellum-NLQ uses a canonical `health-uk` semantic catalogue. A partner insurer
will usually have different physical table and column names. The mapping layer
records how that partner schema lines up with Vellum's canonical tables before
we attempt any runtime SQL rewrite or data onboarding.

This first slice is a readiness check. It validates the mapping file against
the catalogue and reports coverage. It does not yet rewrite generated SQL.

## Example Mapping

The public repository includes a fictional example:

```text
backend/mappings/health-uk/example_insurer.yaml
```

The file maps canonical tables such as `claims`, `claim_lines`, `members`, and
`premium` onto plausible partner source tables.

## Validate It

From the repo root:

```bash
make validate-example-mapping
```

Or from the backend directory:

```bash
python -m app.mapping.validator mappings/health-uk/example_insurer.yaml
```

A valid mapping prints the number of canonical tables and columns covered.

## API Coverage Check

When the backend is running, the same coverage is available through:

```text
GET /mappings/example-insurer/coverage
```

This endpoint is useful for demos and future frontend display. It still only
reports validated coverage; it does not rewrite generated SQL.

## What This Protects

- Unknown canonical tables are rejected.
- Unknown canonical columns are rejected.
- Duplicate canonical table mappings are rejected.
- Duplicate canonical column mappings inside a table are rejected.
- Mapping files must point to the active catalogue they are intended to support.

## Next Step

For a real pilot, the insurer engineering team should provide a non-sensitive
schema inventory. We then create a private mapping file, validate coverage, and
decide whether the missing fields require extraction, transformation, or a
catalogue adjustment.
