from fastapi import APIRouter, HTTPException

from app.analytics.build import build_query
from app.api.ask_schemas import AskRequest as AskApiRequest
from app.api.ask_schemas import AskResponse
from app.api.schemas import (
    MetricResponse,
    MetricsResponse,
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryPreviewRequest,
    QueryPreviewResponse,
)
from app.api.resolve_schemas import QueryResolveRequest, QueryResolveResponse
from app.ask.service import AskRequest as AskServiceRequest
from app.ask.service import answer_question
from app.audit.logger import (
    JsonlAuditLogger,
    build_execution_audit_event,
    build_preview_audit_event,
)
from app.config import get_settings
from app.execution.demo import execute_demo_query
from app.semantic.catalogue import CatalogueError, load_catalogue
from app.semantic.question_resolver import resolve_question
from app.semantic.resolver import ResolutionError


router = APIRouter()


def _load_active_catalogue():
    """Load the active catalogue and convert load failures to HTTP errors."""
    settings = get_settings()
    try:
        return load_catalogue(settings.catalogue_root, settings.active_catalogue)
    except CatalogueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/metrics", response_model=MetricsResponse)
def list_metrics() -> MetricsResponse:
    """Return metric definitions from the active semantic catalogue."""
    catalogue = _load_active_catalogue()

    return MetricsResponse(
        catalogue=catalogue.name,
        metrics=[
            MetricResponse.from_metric(metric)
            for metric in sorted(catalogue.metrics.values(), key=lambda item: item.id)
        ],
    )


@router.post("/ask", response_model=AskResponse)
def ask(request: AskApiRequest) -> AskResponse:
    """Return the ask workspace state for one user question."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        result = answer_question(
            catalogue,
            AskServiceRequest(
                question=request.question,
                start_date=request.start_date,
                end_date=request.end_date,
                plan_tier=request.plan_tier,
            ),
            member_count=settings.demo_member_count,
            month_count=settings.demo_month_count,
        )
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result.build_result is None or result.execution_result is None:
        return AskResponse.from_ask_result(result)

    audit_event = build_execution_audit_event(
        result.resolution.resolved_request,
        result.build_result,
        row_count=result.execution_result.row_count,
        answer=result.execution_result.answer,
    )
    JsonlAuditLogger(settings.audit_log_path).record(audit_event)

    return AskResponse.from_ask_result(result, query_id=audit_event.query_id)


@router.post("/queries/resolve", response_model=QueryResolveResponse)
def resolve_query(request: QueryResolveRequest) -> QueryResolveResponse:
    """Resolve a simple question into a metric or clarification candidates."""
    catalogue = _load_active_catalogue()
    result = resolve_question(
        catalogue,
        question=request.question,
        start_date=request.start_date,
        end_date=request.end_date,
        plan_tier=request.plan_tier,
    )
    return QueryResolveResponse.from_resolution(result)


@router.post("/queries/preview", response_model=QueryPreviewResponse)
def preview_query(request: QueryPreviewRequest) -> QueryPreviewResponse:
    """Return deterministic SQL and provenance without executing the query."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        build_result = build_query(catalogue, request)
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    audit_event = build_preview_audit_event(request, build_result)
    JsonlAuditLogger(settings.audit_log_path).record(audit_event)

    return QueryPreviewResponse.from_build_result(
        build_result,
        query_id=audit_event.query_id,
    )


@router.post("/queries/execute", response_model=QueryExecuteResponse)
def execute_query(request: QueryExecuteRequest) -> QueryExecuteResponse:
    """Execute one guarded deterministic query against local demo data."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        build_result = build_query(catalogue, request)
        execution_result = execute_demo_query(
            build_result,
            member_count=settings.demo_member_count,
            month_count=settings.demo_month_count,
        )
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    audit_event = build_execution_audit_event(
        request,
        build_result,
        row_count=execution_result.row_count,
        answer=execution_result.answer,
    )
    JsonlAuditLogger(settings.audit_log_path).record(audit_event)

    return QueryExecuteResponse.from_execution_result(
        build_result,
        execution_result,
        query_id=audit_event.query_id,
    )


@router.get("/queries/{query_id}")
def get_query(query_id: str) -> dict[str, object]:
    """Return one development audit trace by query ID."""
    settings = get_settings()
    event = JsonlAuditLogger(settings.audit_log_path).find_by_query_id(query_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"query not found: {query_id}")

    return event
