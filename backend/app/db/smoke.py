from dataclasses import dataclass
from datetime import date

from sqlalchemy import create_engine, func, select

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.config import Settings, get_settings
from app.db.checks import all_checks_passed, run_database_checks
from app.db import schema
from app.execution.postgres import execute_postgres_query
from app.semantic.catalogue import load_catalogue


SMOKE_TABLES = (
    schema.plans,
    schema.members,
    schema.providers,
    schema.claims,
    schema.claim_lines,
    schema.premium,
    schema.audit_events,
)

SMOKE_REQUESTS = (
    AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AnalyticsRequest(
        metric_id="paid_claims",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    ),
    AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("consultant_specialty",),
    ),
)


@dataclass(frozen=True)
class SmokeResult:
    """One Postgres smoke-test result."""

    name: str
    passed: bool
    message: str


def run_postgres_smoke(settings: Settings | None = None) -> list[SmokeResult]:
    """Verify the seeded Postgres execution path with guarded generated SQL."""
    active_settings = settings or get_settings()
    results = _database_check_results(active_settings)

    if any(not result.passed for result in results):
        return results

    results.extend(_table_count_results(active_settings))

    if any(not result.passed for result in results):
        return results

    results.extend(_query_execution_results(active_settings))
    return results


def smoke_passed(results: list[SmokeResult]) -> bool:
    """Return whether every smoke-test check passed."""
    return all(result.passed for result in results)


def _database_check_results(settings: Settings) -> list[SmokeResult]:
    checks = run_database_checks(settings)
    results = [
        SmokeResult(
            name=f"db:{check.name}",
            passed=check.passed,
            message=check.message,
        )
        for check in checks
    ]

    if not all_checks_passed(checks):
        results.append(
            SmokeResult(
                name="db:ready",
                passed=False,
                message="database readiness checks failed",
            )
        )

    return results


def _table_count_results(settings: Settings) -> list[SmokeResult]:
    engine = create_engine(settings.readonly_database_url)
    results = []

    with engine.connect() as connection:
        for table in SMOKE_TABLES:
            count = connection.execute(select(func.count()).select_from(table)).scalar_one()
            is_optional_empty = table.name == "audit_events"
            results.append(
                SmokeResult(
                    name=f"table:{table.name}",
                    passed=is_optional_empty or count > 0,
                    message=f"{count:,} rows",
                )
            )

    return results


def _query_execution_results(settings: Settings) -> list[SmokeResult]:
    catalogue = load_catalogue(settings.catalogue_root, settings.active_catalogue)
    results = []

    for request in SMOKE_REQUESTS:
        build_result = build_query(catalogue, request)
        execution = execute_postgres_query(
            build_result,
            database_url=settings.readonly_database_url,
        )
        results.append(
            SmokeResult(
                name=f"query:{request.metric_id}",
                passed=execution.row_count > 0,
                message=(
                    f"{execution.row_count:,} rows through "
                    f"{execution.mode} execution"
                ),
            )
        )

    return results
