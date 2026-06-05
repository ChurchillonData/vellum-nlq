import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock

from app.analytics.models import QueryBuildResult
from app.execution.demo_answers import build_demo_answer
from app.execution.demo_sql import (
    additional_metric_sql,
    claim_frequency_sql,
    claim_severity_sql,
    decline_rate_sql,
    incurred_claims_sql,
    loss_ratio_sql,
    paid_claims_sql,
)
from app.metrics.additional import ADDITIONAL_METRICS
from app.execution.models import ExecutionDatasetSummary, ExecutionResult
from app.execution.sqlite_seed import prepare_demo_database, to_sqlite_parameters
from app.seeds.synthetic import build_seed_data


@dataclass
class DemoDatabase:
    """Cached local demo database for fast repeated in-process queries."""

    connection: sqlite3.Connection
    lock: Lock
    member_count: int
    claim_count: int
    premium_row_count: int


def execute_demo_query(
    build_result: QueryBuildResult,
    member_count: int,
    month_count: int,
) -> ExecutionResult:
    """Run one guarded query against deterministic in-memory demo data."""
    if not build_result.validation.passed:
        raise ValueError("cannot execute SQL that failed guard validation")
    supported_metrics = {
        "loss_ratio",
        "paid_claims",
        "claim_frequency",
        "decline_rate",
        "incurred_claims",
        "claim_severity",
        *ADDITIONAL_METRICS,
    }
    if build_result.provenance.metric_id not in supported_metrics:
        raise ValueError("demo execution does not support this metric yet")

    demo_database = _demo_database(member_count, month_count)
    with demo_database.lock:
        rows = _run_demo_query(demo_database.connection, build_result)

    rows = rows[: build_result.provenance.result_shape.max_rows]
    dataset = ExecutionDatasetSummary(
        name="health-uk synthetic demo",
        member_count=demo_database.member_count,
        claim_count=demo_database.claim_count,
        premium_row_count=demo_database.premium_row_count,
    )
    answer = build_demo_answer(build_result, rows)
    return ExecutionResult(
        rows=rows,
        row_count=len(rows),
        answer=answer,
        dataset=dataset,
        mode="local_demo",
    )


@lru_cache(maxsize=4)
def _demo_database(member_count: int, month_count: int) -> DemoDatabase:
    seed_data = build_seed_data(member_count=member_count, month_count=month_count)
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    prepare_demo_database(connection, seed_data)
    return DemoDatabase(
        connection=connection,
        lock=Lock(),
        member_count=len(seed_data.members),
        claim_count=len(seed_data.claims),
        premium_row_count=len(seed_data.premium),
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
    if build_result.provenance.metric_id == "incurred_claims":
        return _run_incurred_claims_query(connection, build_result)
    if build_result.provenance.metric_id == "claim_severity":
        return _run_claim_severity_query(connection, build_result)
    if build_result.provenance.metric_id in ADDITIONAL_METRICS:
        return _run_additional_metric_query(connection, build_result)
    return _run_loss_ratio_query(connection, build_result)


def _run_loss_ratio_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = loss_ratio_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_paid_claims_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = paid_claims_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_incurred_claims_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = incurred_claims_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_claim_frequency_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = claim_frequency_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]


def _run_claim_severity_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = claim_severity_sql(
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
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


def _run_additional_metric_query(
    connection: sqlite3.Connection,
    build_result: QueryBuildResult,
) -> list[dict[str, object]]:
    parameters = build_result.query.parameters
    sql = additional_metric_sql(
        build_result.provenance.metric_id,
        has_plan_tier=bool(parameters.get("plan_tier")),
        group_by=build_result.plan.group_by,
    )
    rows = connection.execute(sql, to_sqlite_parameters(parameters)).fetchall()
    return [dict(row) for row in rows]
