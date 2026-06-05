from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.analytics.models import AnalyticsRequest
from app.data_window import PeriodAvailability
from app.semantic.question_resolver import MetricCandidate, QuestionResolution
from app.semantic.scope import ScopeFinding
from app.semantic.safety import SafetyFinding


class QueryResolveRequest(BaseModel):
    """Natural-language-like request for deterministic metric resolution."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    start_date: date
    end_date: date
    plan_tier: str | None = Field(default=None, min_length=1)
    group_by: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_date_range(self) -> "QueryResolveRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class MetricCandidateResponse(BaseModel):
    """One metric candidate returned for clarification."""

    metric_id: str
    label: str
    description: str
    confidence: float
    reason: str

    @classmethod
    def from_candidate(cls, candidate: MetricCandidate) -> "MetricCandidateResponse":
        """Convert an internal metric candidate into API JSON."""
        return cls(
            metric_id=candidate.metric_id,
            label=candidate.label,
            description=candidate.description,
            confidence=candidate.confidence,
            reason=candidate.reason,
        )


class SafetyFindingResponse(BaseModel):
    """Safety finding returned when a question is blocked."""

    rule_id: str
    severity: str
    reason: str

    @classmethod
    def from_finding(cls, finding: SafetyFinding) -> "SafetyFindingResponse":
        """Convert a safety finding into API JSON."""
        return cls(
            rule_id=finding.rule_id,
            severity=finding.severity,
            reason=finding.reason,
        )


class ScopeFindingResponse(BaseModel):
    """Scope finding returned when a question is not supported."""

    reason_id: str
    reason: str

    @classmethod
    def from_finding(cls, finding: ScopeFinding) -> "ScopeFindingResponse":
        """Convert a scope finding into API JSON."""
        return cls(reason_id=finding.reason_id, reason=finding.reason)


class PeriodAvailabilityResponse(BaseModel):
    """Data availability finding returned when a period is unavailable."""

    reason_id: str
    message: str

    @classmethod
    def from_finding(
        cls,
        finding: PeriodAvailability,
    ) -> "PeriodAvailabilityResponse":
        """Convert a period availability finding into API JSON."""
        return cls(
            reason_id=finding.reason_id or "period_unavailable",
            message=finding.message or "Requested period is unavailable.",
        )


class QueryResolveResponse(BaseModel):
    """Metric resolution state for the ask workspace."""

    status: str
    question: str
    message: str
    candidates: list[MetricCandidateResponse]
    resolved_request: AnalyticsRequest | None
    safety: SafetyFindingResponse | None
    scope: ScopeFindingResponse | None
    availability: PeriodAvailabilityResponse | None

    @classmethod
    def from_resolution(cls, result: QuestionResolution) -> "QueryResolveResponse":
        """Convert a question resolution into API JSON."""
        return cls(
            status=result.status,
            question=result.question,
            message=result.message,
            candidates=[
                MetricCandidateResponse.from_candidate(candidate)
                for candidate in result.candidates
            ],
            resolved_request=result.resolved_request,
            safety=(
                SafetyFindingResponse.from_finding(result.safety)
                if result.safety is not None
                else None
            ),
            scope=(
                ScopeFindingResponse.from_finding(result.scope)
                if result.scope is not None
                else None
            ),
            availability=(
                PeriodAvailabilityResponse.from_finding(result.availability)
                if result.availability is not None
                else None
            ),
        )
