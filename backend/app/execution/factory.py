from app.analytics.models import QueryBuildResult
from app.config import Settings
from app.execution.demo import execute_demo_query
from app.execution.models import ExecutionResult
from app.execution.postgres import execute_postgres_query


def execute_query(build_result: QueryBuildResult, settings: Settings) -> ExecutionResult:
    """Execute a guarded query with the configured execution backend."""
    if settings.execution_backend == "postgres":
        return execute_postgres_query(
            build_result,
            database_url=settings.readonly_database_url,
        )

    return execute_demo_query(
        build_result,
        member_count=settings.demo_member_count,
        month_count=settings.demo_month_count,
        as_of_date=settings.demo_as_of_date,
    )
