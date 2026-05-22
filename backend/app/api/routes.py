from fastapi import APIRouter, HTTPException

from app.analytics.build import build_query
from app.api.schemas import QueryPreviewRequest, QueryPreviewResponse
from app.config import get_settings
from app.semantic.catalogue import CatalogueError, load_catalogue
from app.semantic.resolver import ResolutionError


router = APIRouter()


@router.post("/queries/preview", response_model=QueryPreviewResponse)
def preview_query(request: QueryPreviewRequest) -> QueryPreviewResponse:
    """Return deterministic SQL and provenance without executing the query."""
    settings = get_settings()

    try:
        catalogue = load_catalogue(settings.catalogue_root, settings.active_catalogue)
        build_result = build_query(catalogue, request)
    except ResolutionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except CatalogueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return QueryPreviewResponse.from_build_result(build_result)
