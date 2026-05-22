from typing import Any

from pydantic import BaseModel

from app.analytics.models import AnalyticsRequest, QueryBuildResult
from app.semantic.models import MetricSpec
from app.sql.guard import SqlGuardResult


class MetricFormulaResponse(BaseModel):
    """Formula fields exposed by the metrics catalogue endpoint."""

    numerator: str
    denominator: str | None
    expression: str


class MetricResponse(BaseModel):
    """One metric definition exposed to API clients."""

    id: str
    label: str
    description: str
    formula: MetricFormulaResponse
    required_tables: list[str]
    time_anchor: str
    currency: str | None
    filters_default: list[str]
    synonyms: list[str]
    owner: str
    version: str
    last_reviewed: str

    @classmethod
    def from_metric(cls, metric: MetricSpec) -> "MetricResponse":
        """Convert a catalogue metric into the public API shape."""
        return cls(
            id=metric.id,
            label=metric.label,
            description=metric.description,
            formula=MetricFormulaResponse(
                numerator=metric.formula.numerator,
                denominator=metric.formula.denominator,
                expression=metric.formula.expression,
            ),
            required_tables=list(metric.required_tables),
            time_anchor=metric.time_anchor,
            currency=metric.currency,
            filters_default=list(metric.filters_default),
            synonyms=list(metric.synonyms),
            owner=metric.owner,
            version=metric.version,
            last_reviewed=metric.last_reviewed,
        )


class MetricsResponse(BaseModel):
    """Loaded metric definitions for the active catalogue."""

    catalogue: str
    metrics: list[MetricResponse]


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


class SqlGuardRejectionResponse(BaseModel):
    """One SQL guard rule failure returned to API callers."""

    rule: str
    message: str


class SqlGuardResponse(BaseModel):
    """SQL validation summary returned with a query preview."""

    passed: bool
    rules_checked: list[str]
    rejections: list[SqlGuardRejectionResponse]

    @classmethod
    def from_guard_result(cls, result: SqlGuardResult) -> "SqlGuardResponse":
        """Convert the internal SQL guard result into API JSON."""
        return cls(
            passed=result.passed,
            rules_checked=list(result.rules_checked),
            rejections=[
                SqlGuardRejectionResponse(rule=item.rule, message=item.message)
                for item in result.rejections
            ],
        )


class QueryPreviewResponse(BaseModel):
    """Previewed SQL and the provenance used to build it."""

    query_id: str
    metric_id: str
    sql: str
    parameters: dict[str, Any]
    provenance: QueryProvenanceResponse
    validation: SqlGuardResponse

    @classmethod
    def from_build_result(
        cls,
        result: QueryBuildResult,
        query_id: str,
    ) -> "QueryPreviewResponse":
        """Convert internal build output into the HTTP response shape."""
        provenance = result.provenance
        return cls(
            query_id=query_id,
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
            validation=SqlGuardResponse.from_guard_result(result.validation),
        )
