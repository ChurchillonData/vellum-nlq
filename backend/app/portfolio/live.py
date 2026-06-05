from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from time import perf_counter

from sqlalchemy import create_engine, func, select

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest
from app.config import Settings, get_settings
from app.db import schema
from app.execution.postgres import execute_postgres_query
from app.portfolio.audit import AuditCheck, expected_claim_count, metric_range_check
from app.semantic.catalogue import load_catalogue


PORTFOLIO_MEMBER_COUNT = 200_000
PORTFOLIO_MONTH_COUNT = 18
PORTFOLIO_START_DATE = date(2025, 1, 1)
PORTFOLIO_END_DATE = date(2026, 6, 30)

LIVE_TABLE_EXPECTATIONS = {
    schema.members: PORTFOLIO_MEMBER_COUNT,
    schema.enrolment_months: PORTFOLIO_MEMBER_COUNT * PORTFOLIO_MONTH_COUNT,
    schema.premium: PORTFOLIO_MEMBER_COUNT * PORTFOLIO_MONTH_COUNT,
    schema.claims: expected_claim_count(PORTFOLIO_MEMBER_COUNT),
}

LIVE_METRICS = ("loss_ratio", "claim_frequency", "claim_severity", "decline_rate")


@dataclass(frozen=True)
class LivePortfolioAuditReport:
    """Quality and latency checks measured against a seeded Postgres database."""

    checks: tuple[AuditCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def audit_live_portfolio(
    settings: Settings | None = None,
    max_latency_ms: float = 5_000,
) -> LivePortfolioAuditReport:
    """Validate portfolio row counts, metrics, and guarded query latency."""
    active_settings = settings or get_settings()
    checks = _table_count_checks(active_settings)
    checks.extend(_query_checks(active_settings, max_latency_ms))
    return LivePortfolioAuditReport(checks=tuple(checks))


def _table_count_checks(settings: Settings) -> list[AuditCheck]:
    engine = create_engine(settings.readonly_database_url)
    checks = []

    with engine.connect() as connection:
        for table, expected in LIVE_TABLE_EXPECTATIONS.items():
            observed = connection.execute(select(func.count()).select_from(table)).scalar_one()
            checks.append(
                AuditCheck(
                    name=f"live-volume:{table.name}",
                    passed=observed == expected,
                    observed=f"{observed:,}",
                    expected=f"{expected:,}",
                )
            )

    return checks


def _query_checks(settings: Settings, max_latency_ms: float) -> list[AuditCheck]:
    catalogue = load_catalogue(settings.catalogue_root, settings.active_catalogue)
    checks = []

    for metric_id in LIVE_METRICS:
        build_result = build_query(
            catalogue,
            AnalyticsRequest(
                metric_id=metric_id,
                start_date=PORTFOLIO_START_DATE,
                end_date=PORTFOLIO_END_DATE,
            ),
        )
        started_at = perf_counter()
        execution = execute_postgres_query(
            build_result,
            database_url=settings.readonly_database_url,
        )
        latency_ms = (perf_counter() - started_at) * 1000
        value = Decimal(str(execution.rows[0][metric_id]))

        checks.append(metric_range_check(metric_id, value))
        checks.append(
            AuditCheck(
                name=f"latency:{metric_id}",
                passed=latency_ms <= max_latency_ms,
                observed=f"{latency_ms:,.1f} ms",
                expected=f"at most {max_latency_ms:,.0f} ms",
            )
        )

    return checks
