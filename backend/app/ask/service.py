from dataclasses import dataclass
from datetime import date
from time import perf_counter

from app.analytics.build import build_query
from app.analytics.models import QueryBuildResult
from app.config import Settings
from app.execution.factory import execute_query
from app.execution.models import ExecutionResult
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
    execution_result: ExecutionResult | None
    planning_ms: float = 0.0
    execution_ms: float = 0.0


def answer_question(
    catalogue: Catalogue,
    request: AskRequest,
    settings: Settings,
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

    planning_started = perf_counter()
    build_result = build_query(catalogue, resolution.resolved_request)
    planning_ms = _elapsed_ms(planning_started)

    execution_started = perf_counter()
    execution_result = execute_query(build_result, settings)
    execution_ms = _elapsed_ms(execution_started)

    return AskResult(
        status="answer",
        resolution=resolution,
        build_result=build_result,
        execution_result=execution_result,
        planning_ms=planning_ms,
        execution_ms=execution_ms,
    )


def _elapsed_ms(started_at: float) -> float:
    """Return elapsed wall-clock time in milliseconds."""
    return round((perf_counter() - started_at) * 1000, 2)
