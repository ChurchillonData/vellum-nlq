from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings


@dataclass(frozen=True)
class DatabaseCheck:
    """One database readiness check result."""

    name: str
    passed: bool
    message: str


def run_database_checks(settings: Settings | None = None) -> list[DatabaseCheck]:
    """Check local Postgres roles used by migrations, seeding, reads, and audit."""
    active_settings = settings or get_settings()
    return [
        _check_connection("admin", active_settings.database_url),
        _check_connection("seeder", active_settings.seed_database_url),
        _check_connection("readonly", active_settings.readonly_database_url),
        _check_connection("auditor", active_settings.audit_database_url),
    ]


def all_checks_passed(checks: list[DatabaseCheck]) -> bool:
    """Return whether every database readiness check passed."""
    return all(check.passed for check in checks)


def _check_connection(name: str, database_url: str) -> DatabaseCheck:
    try:
        engine = create_engine(database_url, connect_args={"connect_timeout": 3})
        with engine.connect() as connection:
            current_user = connection.execute(text("select current_user")).scalar_one()
    except SQLAlchemyError as error:
        return DatabaseCheck(
            name=name,
            passed=False,
            message=_friendly_error(str(error)),
        )

    return DatabaseCheck(
        name=name,
        passed=True,
        message=f"connected as {current_user}",
    )


def _friendly_error(message: str) -> str:
    if "password authentication failed" in message:
        return "password authentication failed"
    if "connection refused" in message or "could not connect" in message:
        return "database is not reachable"
    if "does not exist" in message:
        return "database or role does not exist"
    return message.splitlines()[0]
