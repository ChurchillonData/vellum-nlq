from dataclasses import dataclass
from datetime import date

from app.analytics.build import build_query
from app.analytics.models import QueryBuildResult
from app.execution.demo import DemoExecutionResult, execute_demo_query
from app.semantic.models import Catalogue
from app.semantic.question_resolver import QuestionResolution, resolve_question


@dataclass(frozen=True)
class AskRequest:
    """Question and filters submitted from the ask workspace."""

    question: str
    metric_id: str | None
    start_date: date | None
    end_date: date | None
    plan_tier: str | None
    group_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class AskResult:
    """One product-facing ask result state."""

    status: str
    resolution: QuestionResolution
    build_result: QueryBuildResult | None
    execution_result: DemoExecutionResult | None


def answer_question(
    catalogue: Catalogue,
    request: AskRequest,
    member_count: int,
    month_count: int,
) -> AskResult:
    """Resolve, plan, guard, and execute a question when possible."""
    resolution = resolve_question(
        catalogue,
        question=request.question,
        metric_id=request.metric_id,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
        group_by=request.group_by,
    )

    if resolution.status != "resolved" or resolution.resolved_request is None:
        return AskResult(
            status=resolution.status,
            resolution=resolution,
            build_result=None,
            execution_result=None,
        )

    build_result = build_query(catalogue, resolution.resolved_request)
    execution_result = execute_demo_query(
        build_result,
        member_count=member_count,
        month_count=month_count,
    )
    return AskResult(
        status="answer",
        resolution=resolution,
        build_result=build_result,
        execution_result=execution_result,
    )
