from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.semantic.models import JoinEdge, MetricSpec


class AnalyticsRequest(BaseModel):
    """A structured analytics request before any LLM layer is involved."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str
    start_date: date
    end_date: date
    plan_tier: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_date_range(self) -> "AnalyticsRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


@dataclass(frozen=True)
class ResolvedRequest:
    """A request after its metric has been checked against the catalogue."""

    request: AnalyticsRequest
    metric: MetricSpec


@dataclass(frozen=True)
class ResultShape:
    """The columns and grain expected from a generated query."""

    columns: tuple[str, ...]
    grain: str


@dataclass(frozen=True)
class LogicalPlan:
    """A small deterministic plan for one catalogue-backed metric query."""

    metric: MetricSpec
    start_date: date
    end_date: date
    plan_tier: str | None
    tables: tuple[str, ...]
    joins: tuple[JoinEdge, ...]
    filters: tuple[str, ...]
    result_shape: ResultShape


@dataclass(frozen=True)
class GeneratedQuery:
    """Parameterised SQL and the parameters that belong with it."""

    sql: str
    parameters: dict[str, object]


@dataclass(frozen=True)
class QueryProvenance:
    """Catalogue and plan details that explain a generated query."""

    metric_id: str
    metric_label: str
    metric_version: str
    metric_description: str
    formula: str
    time_anchor: str
    tables_used: tuple[str, ...]
    joins_used: tuple[str, ...]
    result_shape: ResultShape


@dataclass(frozen=True)
class QueryBuildResult:
    """The deterministic output produced before query execution."""

    plan: LogicalPlan
    query: GeneratedQuery
    provenance: QueryProvenance

