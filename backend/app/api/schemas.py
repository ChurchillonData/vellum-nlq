from typing import Any

from pydantic import BaseModel

from app.analytics.models import AnalyticsRequest, QueryBuildResult


class QueryPreviewRequest(AnalyticsRequest):
    """Structured request body for deterministic SQL preview."""


class ResultShapeResponse(BaseModel):
    """Expected columns and grain for a previewed query."""

    columns: list[str]
    grain: str


class QueryProvenanceResponse(BaseModel):
    """Catalogue details returned with a previewed query."""

    metric_label: str
    metric_version: str
    metric_description: str
    formula: str
    time_anchor: str
    tables_used: list[str]
    joins_used: list[str]
    result_shape: ResultShapeResponse


class QueryPreviewResponse(BaseModel):
    """Previewed SQL and the provenance used to build it."""

    metric_id: str
    sql: str
    parameters: dict[str, Any]
    provenance: QueryProvenanceResponse

    @classmethod
    def from_build_result(cls, result: QueryBuildResult) -> "QueryPreviewResponse":
        """Convert internal build output into the HTTP response shape."""
        provenance = result.provenance
        return cls(
            metric_id=provenance.metric_id,
            sql=result.query.sql,
            parameters=result.query.parameters,
            provenance=QueryProvenanceResponse(
                metric_label=provenance.metric_label,
                metric_version=provenance.metric_version,
                metric_description=provenance.metric_description,
                formula=provenance.formula,
                time_anchor=provenance.time_anchor,
                tables_used=list(provenance.tables_used),
                joins_used=list(provenance.joins_used),
                result_shape=ResultShapeResponse(
                    columns=list(provenance.result_shape.columns),
                    grain=provenance.result_shape.grain,
                ),
            ),
        )
