# Portfolio Audit

The portfolio audit proves that Vellum-NLQ's synthetic demo data is both large
and analytically credible. It is separate from ordinary unit tests because the
full generated profile contains 200,000 members across 18 months.

## Generated Portfolio Audit

Run the audit without Postgres:

```bash
make portfolio-audit
```

Windows users can run the same workflow from `backend/`:

```powershell
python -m app.portfolio_audit
```

The command generates the profile in chunks and retains only streaming
aggregates. It verifies:

- 200,000 members and 18 coverage months.
- 3.6 million enrolment-month and premium rows.
- The deterministic expected claim count.
- Loss ratio between 0.78 and 0.92.
- Claim frequency between 90 and 115 claims per thousand member-months.
- Claim severity between GBP 2,500 and GBP 3,300.
- Decline rate between 5% and 8%.
- Generation duration and aggregate rows per second.

For a quick development check, use smaller values:

```powershell
python -m app.portfolio_audit --member-count 1000 --chunk-size 500
```

## Live Postgres Audit

After loading the portfolio profile into Postgres, run:

```bash
make portfolio-audit-live
```

The live audit connects through the read-only role. It validates the main table
counts, runs the four representative metrics through the normal catalogue,
planner, SQL guard, and Postgres executor, and checks each query against a
five-second latency ceiling.

The ceiling is deliberately conservative for laptops and small hosted
instances. Override it when testing a defined service-level target:

```powershell
python -m app.portfolio_audit --live --max-latency-ms 2000
```

The live command does not seed or modify data. Load the portfolio first with
`make seed-portfolio-data`.
