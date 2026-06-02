from typing import Any

from pydantic import BaseModel

from app.analytics.models import AnalyticsRequest, QueryBuildResult
from app.execution.models import ExecutionResult
from app.mapping.models import MappingCoverage
from app.planner.grouping import COMMON_GROUPINGS
from app.semantic.models import Catalogue, JoinEdge, MetricSpec
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
    allowed_dimensions: list[str]
    join_preview: list[str]

    @classmethod
    def from_metric(
        cls,
        metric: MetricSpec,
        catalogue: Catalogue | None = None,
    ) -> "MetricResponse":
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
            allowed_dimensions=_allowed_dimensions(metric),
            join_preview=(
                _join_preview(metric, catalogue.joins)
                if catalogue is not None
                else []
            ),
        )


class MetricsResponse(BaseModel):
    """Loaded metric definitions for the active catalogue."""

    catalogue: str
    metrics: list[MetricResponse]


class MappingCoverageResponse(BaseModel):
    """Partner schema mapping coverage exposed to API clients."""

    partner: str
    catalogue: str
    mapped_tables: int
    total_tables: int
    mapped_columns: int
    total_columns: int
    missing_tables: list[str]
    missing_columns: list[str]

    @classmethod
    def from_coverage(cls, coverage: MappingCoverage) -> "MappingCoverageResponse":
        """Convert internal mapping coverage into the HTTP response shape."""
        return cls(**coverage.model_dump())


def _allowed_dimensions(metric: MetricSpec) -> list[str]:
    """Return the frontend-safe grouping dimensions for one metric."""
    dimensions = sorted(COMMON_GROUPINGS)
    if metric.id == "decline_rate":
        dimensions.append("consultant_specialty")
    return dimensions


def _join_preview(metric: MetricSpec, joins: list[JoinEdge]) -> list[str]:
    """Return a readable preview of catalogue join edges relevant to a metric."""
    relevant_tables = set(metric.required_tables)
    relevant_tables.add(metric.time_anchor_parts[0])

    if "claim_lines" in relevant_tables:
        relevant_tables.add("claims")

    if {"claims", "premium", "enrolment_months"} & relevant_tables:
        relevant_tables.add("members")

    if {"plan_tier", "region"} & set(_allowed_dimensions(metric)):
        relevant_tables.update({"members", "plans"})

    if metric.id == "decline_rate":
        relevant_tables.update({"claim_lines", "providers", "declines"})

    previews = [
        (
            f"{join.left_table}.{join.left_column} -> "
            f"{join.right_table}.{join.right_column} ({join.cardinality})"
        )
        for join in joins
        if join.left_table in relevant_tables and join.right_table in relevant_tables
    ]

    return previews


class QueryPreviewRequest(AnalyticsRequest):
    """Structured request body for deterministic SQL preview."""


class QueryExecuteRequest(AnalyticsRequest):
    """Structured request body for local demo query execution."""


class ResultShapeResponse(BaseModel):
    """Expected columns and grain for a previewed query."""

    columns: list[str]
    grain: str
    max_rows: int


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


class QueryLatencyResponse(BaseModel):
    """Measured request timings in milliseconds."""

    planning_ms: float
    execution_ms: float | None
    total_ms: float


class QueryPreviewResponse(BaseModel):
    """Previewed SQL and the provenance used to build it."""

    query_id: str
    metric_id: str
    sql: str
    compact_sql: str
    parameters: dict[str, Any]
    provenance: QueryProvenanceResponse
    validation: SqlGuardResponse
    latency: QueryLatencyResponse

    @classmethod
    def from_build_result(
        cls,
        result: QueryBuildResult,
        query_id: str,
        planning_ms: float,
    ) -> "QueryPreviewResponse":
        """Convert internal build output into the HTTP response shape."""
        provenance = result.provenance
        return cls(
            query_id=query_id,
            metric_id=provenance.metric_id,
            sql=result.query.sql,
            compact_sql=result.query.compact_sql,
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
                    max_rows=provenance.result_shape.max_rows,
                ),
            ),
            validation=SqlGuardResponse.from_guard_result(result.validation),
            latency=QueryLatencyResponse(
                planning_ms=planning_ms,
                execution_ms=None,
                total_ms=planning_ms,
            ),
        )


class DemoDatasetResponse(BaseModel):
    """Description of the local demo dataset used for execution."""

    name: str
    member_count: int | None
    claim_count: int | None
    premium_row_count: int | None


class QueryExecuteResponse(QueryPreviewResponse):
    """Executed demo query, result rows, and provenance."""

    answer: str
    rows: list[dict[str, Any]]
    row_count: int
    execution_mode: str
    dataset: DemoDatasetResponse

    @classmethod
    def from_execution_result(
        cls,
        build_result: QueryBuildResult,
        execution_result: ExecutionResult,
        query_id: str,
        planning_ms: float,
        execution_ms: float,
    ) -> "QueryExecuteResponse":
        """Convert executed query output into the HTTP response shape."""
        preview = QueryPreviewResponse.from_build_result(
            build_result,
            query_id=query_id,
            planning_ms=planning_ms,
        )
        preview_payload = preview.model_dump()
        preview_payload["latency"] = QueryLatencyResponse(
            planning_ms=planning_ms,
            execution_ms=execution_ms,
            total_ms=round(planning_ms + execution_ms, 2),
        )
        return cls(
            **preview_payload,
            answer=execution_result.answer,
            rows=execution_result.rows,
            row_count=execution_result.row_count,
            execution_mode=execution_result.mode,
            dataset=DemoDatasetResponse(
                name=execution_result.dataset.name,
                member_count=execution_result.dataset.member_count,
                claim_count=execution_result.dataset.claim_count,
                premium_row_count=execution_result.dataset.premium_row_count,
            ),
        )
