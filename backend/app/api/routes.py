from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.analytics.build import build_query
from app.api.ask_schemas import AskExampleResponse, AskExamplesResponse
from app.api.ask_schemas import AskRequest as AskApiRequest
from app.api.ask_schemas import AskResponse
from app.api.schemas import (
    MappingCoverageResponse,
    MetricResponse,
    MetricsResponse,
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryPreviewRequest,
    QueryPreviewResponse,
)
from app.api.resolve_schemas import QueryResolveRequest, QueryResolveResponse
from app.ask.examples import GOLDEN_ASK_EXAMPLES
from app.ask.parser import parse_ask_fields
from app.ask.service import AskRequest as AskServiceRequest
from app.ask.service import answer_question
from app.audit.logger import (
    build_ask_audit_event,
    build_execution_audit_event,
    build_preview_audit_event,
)
from app.audit.store import build_audit_store
from app.config import get_settings
from app.execution.factory import execute_query as execute_configured_query
from app.intent.factory import build_intent_provider
from app.intent.models import IntentProviderError
from app.mapping.models import SchemaMapping
from app.mapping.validator import (
    MappingError,
    load_schema_mapping,
    validate_schema_mapping,
)
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
            MetricResponse.from_metric(metric, catalogue)
            for metric in sorted(catalogue.metrics.values(), key=lambda item: item.id)
        ],
    )


@router.get("/mappings/{partner}/coverage", response_model=MappingCoverageResponse)
def get_mapping_coverage(partner: str) -> MappingCoverageResponse:
    """Return validated coverage for one partner schema mapping."""
    catalogue = _load_active_catalogue()
    mapping = _load_partner_mapping(partner)

    try:
        coverage = validate_schema_mapping(catalogue, mapping)
    except MappingError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return MappingCoverageResponse.from_coverage(coverage)


@router.get("/ask/examples", response_model=AskExamplesResponse)
def list_ask_examples() -> AskExamplesResponse:
    """Return golden ask questions for demos and contract tests."""
    return AskExamplesResponse(
        examples=[
            AskExampleResponse.from_example(example)
            for example in GOLDEN_ASK_EXAMPLES
        ]
    )


def _load_partner_mapping(partner: str) -> SchemaMapping:
    """Load a partner mapping from the active catalogue mapping directory."""
    settings = get_settings()
    mapping_dir = settings.mapping_root / settings.active_catalogue
    preferred_path = mapping_dir / f"{partner.replace('-', '_')}.yaml"
    candidate_paths = (
        [preferred_path]
        if preferred_path.exists()
        else sorted(mapping_dir.glob("*.yaml"))
    )

    for mapping_path in candidate_paths:
        try:
            mapping = load_schema_mapping(mapping_path)
        except MappingError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        if mapping.partner == partner:
            return mapping

    raise HTTPException(status_code=404, detail=f"mapping not found: {partner}")


@router.post("/ask", response_model=AskResponse)
def ask(request: AskApiRequest) -> AskResponse:
    """Return the ask workspace state for one user question."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        intent = build_intent_provider(settings).extract_intent(
            catalogue,
            request.question,
        )
        parsed_fields = parse_ask_fields(request.question)
        ask_request = AskServiceRequest(
            question=request.question,
            metric_id=request.metric_id or intent.metric_id,
            start_date=(
                request.start_date or intent.start_date or parsed_fields.start_date
            ),
            end_date=request.end_date or intent.end_date or parsed_fields.end_date,
            plan_tier=request.plan_tier or intent.plan_tier or parsed_fields.plan_tier,
            group_by=request.group_by or intent.group_by or parsed_fields.group_by,
        )
        result = answer_question(
            catalogue,
            ask_request,
            settings=settings,
        )
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except IntentProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    audit_event = build_ask_audit_event(ask_request, result)
    build_audit_store(settings).record(audit_event)

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
        group_by=request.group_by,
    )
    return QueryResolveResponse.from_resolution(result)


@router.post("/queries/preview", response_model=QueryPreviewResponse)
def preview_query(request: QueryPreviewRequest) -> QueryPreviewResponse:
    """Return deterministic SQL and provenance without executing the query."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        planning_started = perf_counter()
        build_result = build_query(catalogue, request)
        planning_ms = _elapsed_ms(planning_started)
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    audit_event = build_preview_audit_event(request, build_result)
    build_audit_store(settings).record(audit_event)

    return QueryPreviewResponse.from_build_result(
        build_result,
        query_id=audit_event.query_id,
        planning_ms=planning_ms,
    )


@router.post("/queries/execute", response_model=QueryExecuteResponse)
def execute_query(request: QueryExecuteRequest) -> QueryExecuteResponse:
    """Execute one guarded deterministic query against local demo data."""
    settings = get_settings()

    try:
        catalogue = _load_active_catalogue()
        planning_started = perf_counter()
        build_result = build_query(catalogue, request)
        planning_ms = _elapsed_ms(planning_started)
        execution_started = perf_counter()
        execution_result = execute_configured_query(build_result, settings)
        execution_ms = _elapsed_ms(execution_started)
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    audit_event = build_execution_audit_event(
        request,
        build_result,
        row_count=execution_result.row_count,
        answer=execution_result.answer,
        mode=execution_result.mode,
    )
    build_audit_store(settings).record(audit_event)

    return QueryExecuteResponse.from_execution_result(
        build_result,
        execution_result,
        query_id=audit_event.query_id,
        planning_ms=planning_ms,
        execution_ms=execution_ms,
    )


@router.get("/queries/{query_id}")
def get_query(query_id: str) -> dict[str, object]:
    """Return one development audit trace by query ID."""
    settings = get_settings()
    event = build_audit_store(settings).find_by_query_id(query_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"query not found: {query_id}")

    return event


def _elapsed_ms(started_at: float) -> float:
    """Return elapsed wall-clock time in milliseconds."""
    return round((perf_counter() - started_at) * 1000, 2)
