from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.analytics.models import AnalyticsRequest
from app.semantic.question_resolver import MetricCandidate, QuestionResolution


class QueryResolveRequest(BaseModel):
    """Natural-language-like request for deterministic metric resolution."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    start_date: date
    end_date: date
    plan_tier: str | None = Field(default=None, min_length=1)

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


class QueryResolveResponse(BaseModel):
    """Metric resolution state for the ask workspace."""

    status: str
    question: str
    message: str
    candidates: list[MetricCandidateResponse]
    resolved_request: AnalyticsRequest | None

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
        )

