# Local Postgres

This project uses local Postgres for the real database foundation before cloud
hosting is added.

## Roles

The local Docker database creates three roles:

- `vellum_admin`: owns setup and runs Alembic migrations.
- `vellum_seeder`: loads synthetic development data.
- `vellum_readonly`: future application execution role with SELECT-only access.

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
make seed-data
make db-shell
make db-shell-admin
make db-shell-seed
```

## Connection URLs

The backend has separate URLs for each database responsibility:

```text
VELLUM_DATABASE_URL          # admin / migrations
VELLUM_SEED_DATABASE_URL     # synthetic seed loading
VELLUM_READONLY_DATABASE_URL # future guarded query execution
```

Local defaults are defined in `backend/app/config.py`.

## Current Boundary

The local Postgres schema, roles, migrations, seed path, and guarded Postgres
executor are now in place. The API still defaults to the in-memory demo executor
so the project runs without Docker.

To execute guarded generated SQL against local Postgres, set:

```text
VELLUM_EXECUTION_BACKEND=postgres
```

The Postgres execution path uses `VELLUM_READONLY_DATABASE_URL`, refuses SQL
that failed guard validation, and passes generated parameters as bound values.

The next backend storage slice is the append-only Postgres audit table.
