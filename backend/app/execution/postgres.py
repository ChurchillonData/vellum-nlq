from sqlalchemy import create_engine, text

from app.analytics.models import QueryBuildResult
from app.execution.demo_answers import build_demo_answer
from app.execution.models import ExecutionDatasetSummary, ExecutionResult


def execute_postgres_query(
    build_result: QueryBuildResult,
    database_url: str,
) -> ExecutionResult:
    """Run one guarded generated query against Postgres."""
    if not build_result.validation.passed:
        raise ValueError("cannot execute SQL that failed guard validation")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        rows = [
            dict(row._mapping)
            for row in connection.execute(
                text(build_result.query.sql),
                build_result.query.parameters,
            ).fetchall()
        ]

    rows = rows[: build_result.provenance.result_shape.max_rows]
    answer = build_demo_answer(build_result, rows)
    return ExecutionResult(
        rows=rows,
        row_count=len(rows),
        answer=answer,
        dataset=ExecutionDatasetSummary(
            name="health-uk postgres",
            member_count=None,
            claim_count=None,
            premium_row_count=None,
        ),
        mode="postgres",
    )
