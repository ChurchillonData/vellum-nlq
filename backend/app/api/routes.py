from fastapi import APIRouter, HTTPException

from app.analytics.build import build_query
from app.api.schemas import (
    MetricResponse,
    MetricsResponse,
    QueryPreviewRequest,
    QueryPreviewResponse,
)
from app.audit.logger import JsonlAuditLogger, build_preview_audit_event
from app.config import get_settings
from app.semantic.catalogue import CatalogueError, load_catalogue
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


@router.get("/queries/{query_id}")
def get_query(query_id: str) -> dict[str, object]:
    """Return one development audit trace by query ID."""
    settings = get_settings()
    event = JsonlAuditLogger(settings.audit_log_path).find_by_query_id(query_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"query not found: {query_id}")

    return event
