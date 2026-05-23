import sqlite3
from dataclasses import dataclass

from app.analytics.models import QueryBuildResult
from app.execution.sqlite_seed import prepare_demo_database, to_sqlite_parameters
from app.seeds.synthetic import build_seed_data


@dataclass(frozen=True)
class DemoDatasetSummary:
    """Small description of the seeded demo dataset used for execution."""

    name: str
    member_count: int
    claim_count: int
    premium_row_count: int


@dataclass(frozen=True)
class DemoExecutionResult:
    """Rows and summary produced by local demo execution."""

    rows: list[dict[str, object]]
    row_count: int
    answer: str
    dataset: DemoDatasetSummary


def execute_demo_query(
    build_result: QueryBuildResult,
    member_count: int,
    month_count: int,
) -> DemoExecutionResult:
    """Run one guarded query against deterministic in-memory demo data."""
    if not build_result.validation.passed:
        raise ValueError("cannot execute SQL that failed guard validation")
    if build_result.provenance.metric_id != "loss_ratio":
        raise ValueError("demo execution currently supports loss_ratio only")

    seed_data = build_seed_data(member_count=member_count, month_count=month_count)
    with sqlite3.connect(":memory:") as connection:
        connection.row_factory = sqlite3.Row
        prepare_demo_database(connection, seed_data)
        rows = _run_loss_ratio_query(connection, build_result)

    dataset = DemoDatasetSummary(
        name="health-uk synthetic demo",
        member_count=len(seed_data.members),
        claim_count=len(seed_data.claims),
        premium_row_count=len(seed_data.premium),
    )
    return DemoExecutionResult(
        rows=rows,
        row_count=len(rows),
        answer=_build_loss_ratio_answer(build_result, rows),
        dataset=dataset,
    )


def _run_loss_ratio_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = _loss_ratio_sql(has_plan_tier=bool(parameters.get("plan_tier")))
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _loss_ratio_sql(has_plan_tier: bool) -> str:
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    return f"""
        WITH claim_totals AS (
            SELECT
                claims.member_id AS member_id,
                SUM(claims.net_incurred_amount) AS incurred_claims
            FROM claims
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE claims.incurred_date BETWEEN :start_date AND :end_date
              AND claims.status != :excluded_status
              {plan_filter}
            GROUP BY claims.member_id
        ),
        premium_totals AS (
            SELECT
                premium.member_id AS member_id,
                SUM(premium.earned_amount) AS earned_premium
            FROM premium
            JOIN members ON premium.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE premium.coverage_month BETWEEN :start_date AND :end_date
              {plan_filter}
            GROUP BY premium.member_id
        )
        SELECT
            SUM(claim_totals.incurred_claims)
            / NULLIF(SUM(premium_totals.earned_premium), 0) AS loss_ratio
        FROM claim_totals
        JOIN premium_totals ON claim_totals.member_id = premium_totals.member_id
    """


def _build_loss_ratio_answer(
    build_result: QueryBuildResult,
    rows: list[dict[str, object]],
) -> str:
    value = rows[0].get("loss_ratio") if rows else None
    plan_tier = build_result.plan.plan_tier
    period = (
        f"{build_result.plan.start_date.isoformat()} "
        f"to {build_result.plan.end_date.isoformat()}"
    )
    subject = f"{plan_tier} plan tier loss ratio" if plan_tier else "Loss ratio"

    if value is None:
        return f"{subject} from {period} could not be calculated because premium was zero."

    ratio = float(value)
    return f"{subject} from {period} was {ratio:.3f} ({ratio:.1%})."
