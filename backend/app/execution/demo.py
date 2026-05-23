import sqlite3
from dataclasses import dataclass

from app.analytics.models import QueryBuildResult
from app.execution.demo_answers import build_demo_answer
from app.execution.demo_sql import (
    claim_frequency_sql,
    decline_rate_sql,
    loss_ratio_sql,
    paid_claims_sql,
)
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
    supported_metrics = {
        "loss_ratio",
        "paid_claims",
        "claim_frequency",
        "decline_rate",
    }
    if build_result.provenance.metric_id not in supported_metrics:
        raise ValueError("demo execution does not support this metric yet")

    seed_data = build_seed_data(member_count=member_count, month_count=month_count)
    with sqlite3.connect(":memory:") as connection:
        connection.row_factory = sqlite3.Row
        prepare_demo_database(connection, seed_data)
        rows = _run_demo_query(connection, build_result)

    dataset = DemoDatasetSummary(
        name="health-uk synthetic demo",
        member_count=len(seed_data.members),
        claim_count=len(seed_data.claims),
        premium_row_count=len(seed_data.premium),
    )
    answer = build_demo_answer(build_result, rows)
    return DemoExecutionResult(
        rows=rows,
        row_count=len(rows),
        answer=answer,
        dataset=dataset,
    )


def _run_demo_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    if build_result.provenance.metric_id == "claim_frequency":
        return _run_claim_frequency_query(connection, build_result)
    if build_result.provenance.metric_id == "decline_rate":
        return _run_decline_rate_query(connection, build_result)
    if build_result.provenance.metric_id == "paid_claims":
        return _run_paid_claims_query(connection, build_result)
    return _run_loss_ratio_query(connection, build_result)


def _run_loss_ratio_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = loss_ratio_sql(has_plan_tier=bool(parameters.get("plan_tier")))
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_paid_claims_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = paid_claims_sql(has_plan_tier=bool(parameters.get("plan_tier")))
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_claim_frequency_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = claim_frequency_sql(has_plan_tier=bool(parameters.get("plan_tier")))
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_decline_rate_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = decline_rate_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]
