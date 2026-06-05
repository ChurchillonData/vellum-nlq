from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import cast

from app.seeds.synthetic import SeedData, build_seed_data


SEED_TABLES = (
    "plans",
    "members",
    "providers",
    "enrolment_months",
    "claims",
    "claim_lines",
    "claim_status_history",
    "reserves",
    "premium",
    "declines",
)

METRIC_RANGES = {
    "loss_ratio": (Decimal("0.78"), Decimal("0.92")),
    "claim_frequency": (Decimal("90"), Decimal("115")),
    "claim_severity": (Decimal("2500"), Decimal("3300")),
    "decline_rate": (Decimal("0.05"), Decimal("0.08")),
}


@dataclass(frozen=True)
class AuditCheck:
    """One observable portfolio contract and its outcome."""

    name: str
    passed: bool
    observed: str
    expected: str


@dataclass
class PortfolioSummary:
    """Streaming aggregates collected without retaining the full portfolio."""

    row_counts: dict[str, int] = field(
        default_factory=lambda: {table_name: 0 for table_name in SEED_TABLES}
    )
    coverage_months: set[date] = field(default_factory=set)
    incurred_total: Decimal = Decimal("0")
    premium_total: Decimal = Decimal("0")
    closed_paid_total: Decimal = Decimal("0")
    closed_claim_count: int = 0
    generation_seconds: float = 0

    @property
    def loss_ratio(self) -> Decimal:
        return _divide(self.incurred_total, self.premium_total)

    @property
    def claim_frequency(self) -> Decimal:
        claim_count = Decimal(self.row_counts["claims"]) * Decimal("1000")
        return _divide(claim_count, Decimal(self.row_counts["enrolment_months"]))

    @property
    def claim_severity(self) -> Decimal:
        return _divide(self.closed_paid_total, Decimal(self.closed_claim_count))

    @property
    def decline_rate(self) -> Decimal:
        return _divide(
            Decimal(self.row_counts["declines"]),
            Decimal(self.row_counts["claim_lines"]),
        )

    @property
    def generated_rows_per_second(self) -> int:
        total_rows = sum(self.row_counts.values())
        return round(total_rows / self.generation_seconds) if self.generation_seconds else 0


@dataclass(frozen=True)
class PortfolioAuditReport:
    """Quality and generation-performance report for one synthetic profile."""

    summary: PortfolioSummary
    checks: tuple[AuditCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def audit_generated_portfolio(
    member_count: int = 200_000,
    month_count: int = 18,
    chunk_size: int = 10_000,
) -> PortfolioAuditReport:
    """Generate a profile in chunks and validate its row shape and distributions."""
    if member_count < 1 or month_count < 1 or chunk_size < 1:
        raise ValueError("portfolio audit counts must be at least 1")

    summary = PortfolioSummary()
    started_at = perf_counter()

    for start_index in range(0, member_count, chunk_size):
        current_size = min(chunk_size, member_count - start_index)
        seed_data = build_seed_data(
            member_count=current_size,
            month_count=month_count,
            start_member_index=start_index,
            include_reference_data=start_index == 0,
        )
        add_seed_data(summary, seed_data)

    summary.generation_seconds = perf_counter() - started_at
    checks = build_quality_checks(summary, member_count, month_count)
    return PortfolioAuditReport(summary=summary, checks=tuple(checks))


def add_seed_data(summary: PortfolioSummary, seed_data: SeedData) -> None:
    """Add one generated seed chunk to streaming portfolio aggregates."""
    for table_name in SEED_TABLES:
        summary.row_counts[table_name] += len(getattr(seed_data, table_name))

    summary.coverage_months.update(
        cast(date, row["coverage_month"]) for row in seed_data.premium
    )
    summary.incurred_total += sum(
        (_as_decimal(row["net_incurred_amount"]) for row in seed_data.claims),
        Decimal("0"),
    )
    summary.premium_total += sum(
        (_as_decimal(row["earned_amount"]) for row in seed_data.premium),
        Decimal("0"),
    )

    closed_claim_ids = {row["id"] for row in seed_data.claims if row["status"] == "closed"}
    summary.closed_claim_count += len(closed_claim_ids)
    summary.closed_paid_total += sum(
        (
            _as_decimal(row["net_paid_amount"])
            for row in seed_data.claim_lines
            if row["claim_id"] in closed_claim_ids
        ),
        Decimal("0"),
    )


def build_quality_checks(
    summary: PortfolioSummary,
    expected_members: int,
    expected_months: int,
) -> list[AuditCheck]:
    """Build explicit volume and metric-distribution checks."""
    expected_member_months = expected_members * expected_months
    checks = [
        _exact_check("members", summary.row_counts["members"], expected_members),
        _exact_check("coverage_months", len(summary.coverage_months), expected_months),
        _exact_check(
            "enrolment_months",
            summary.row_counts["enrolment_months"],
            expected_member_months,
        ),
        _exact_check("premium_rows", summary.row_counts["premium"], expected_member_months),
        _exact_check(
            "claims",
            summary.row_counts["claims"],
            expected_claim_count(expected_members),
        ),
    ]
    checks.extend(
        [
            metric_range_check("loss_ratio", summary.loss_ratio),
            metric_range_check("claim_frequency", summary.claim_frequency),
            metric_range_check("claim_severity", summary.claim_severity),
            metric_range_check("decline_rate", summary.decline_rate),
        ]
    )
    return checks


def expected_claim_count(member_count: int) -> int:
    """Return the deterministic number of claims generated for a member count."""
    divisors = (1, 2, 4, 10)
    return sum(((member_count - 1) // divisor) + 1 for divisor in divisors)


def metric_range_check(metric_id: str, value: Decimal) -> AuditCheck:
    """Validate one metric against the documented portfolio target range."""
    lower, upper = METRIC_RANGES[metric_id]
    return AuditCheck(
        name=f"metric:{metric_id}",
        passed=lower <= value <= upper,
        observed=_format_decimal(value),
        expected=f"{_format_decimal(lower)} to {_format_decimal(upper)}",
    )


def _exact_check(name: str, observed: int, expected: int) -> AuditCheck:
    return AuditCheck(
        name=f"volume:{name}",
        passed=observed == expected,
        observed=f"{observed:,}",
        expected=f"{expected:,}",
    )


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    return numerator / denominator if denominator else Decimal("0")


def _as_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.001')):,}"
