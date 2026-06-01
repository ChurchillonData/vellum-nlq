from app.db.smoke import run_postgres_smoke, smoke_passed


def main() -> None:
    """Run the Postgres smoke test for seeded local or portfolio data."""
    results = run_postgres_smoke()

    for result in results:
        status = "ok" if result.passed else "failed"
        print(f"{result.name}: {status} - {result.message}")

    if not smoke_passed(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
