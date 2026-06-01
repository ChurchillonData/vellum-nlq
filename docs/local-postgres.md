# Local Postgres

This project uses local Postgres for the real database foundation before cloud
hosting is added.

## Roles

The local Docker database creates four roles:

- `vellum_admin`: owns setup and runs Alembic migrations.
- `vellum_seeder`: loads synthetic development data.
- `vellum_readonly`: application execution role with SELECT-only access.
- `vellum_auditor`: writes and reads audit events with no update/delete grants.

`vellum_readonly` also has local database defaults for `statement_timeout` and
`work_mem`.

## Start And Seed

From the repository root:

```bash
make seed
```

This starts the Postgres container, runs Alembic migrations, loads deterministic
synthetic data, and validates the active catalogue.

Useful commands:

```bash
make up-detached
make migrate
make db-check
make seed-data
make db-shell
make db-shell-admin
make db-shell-seed
```

Run `make db-check` before portfolio seeding. It verifies the admin, seeder,
read-only, and audit connection URLs separately, so password or role mistakes
show up before a large load begins.

## Connection URLs

The backend has separate URLs for each database responsibility:

```text
VELLUM_DATABASE_URL          # admin / migrations
VELLUM_SEED_DATABASE_URL     # synthetic seed loading
VELLUM_READONLY_DATABASE_URL # guarded query execution
VELLUM_AUDIT_DATABASE_URL    # append-only audit storage
```

Local defaults are defined in `backend/app/config.py`.

## Current Boundary

The local Postgres schema, roles, migrations, seed path, guarded Postgres
executor, and append-only audit table are now in place. The API still defaults
to the in-memory demo executor and JSONL audit store so the project runs without
Docker.

To execute guarded generated SQL against local Postgres, set:

```text
VELLUM_EXECUTION_BACKEND=postgres
```

The Postgres execution path uses `VELLUM_READONLY_DATABASE_URL`, refuses SQL
that failed guard validation, and passes generated parameters as bound values.

To store audit events in Postgres, set:

```text
VELLUM_AUDIT_BACKEND=postgres
```

That path uses `VELLUM_AUDIT_DATABASE_URL` and writes to `audit_events` through
the `vellum_auditor` role. The local grant is SELECT and INSERT only.

## Synthetic Data Profiles

The default seed command uses the small local profile:

```bash
make seed-data
```

That generates 2,000 members across 18 months. It is intentionally quick and is
the right profile for normal development and tests.

For the portfolio demo, use:

```bash
make seed-portfolio-data
```

That runs `backend/seeds/generate.py --profile portfolio`, which generates
200,000 members across 18 months. The portfolio profile loads data in 10,000
member chunks so the seeding process does not need to hold millions of premium
and enrolment rows in memory at once.

You can override the profile values when needed:

```bash
cd backend
python seeds/generate.py --profile portfolio --member-count 50000 --chunk-size 5000
```

To verify the expected volume without touching the database, add `--dry-run`:

```bash
cd backend
python seeds/generate.py --profile portfolio --dry-run
```

Use the portfolio profile for demo/performance preparation, not for ordinary
inner-loop development.
