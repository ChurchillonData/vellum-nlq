from app.db.checks import all_checks_passed, run_database_checks


def main() -> None:
    """Run local Postgres readiness checks for demo and portfolio seeding."""
    checks = run_database_checks()

    for check in checks:
        status = "ok" if check.passed else "failed"
        print(f"{check.name}: {status} - {check.message}")

    if not all_checks_passed(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
