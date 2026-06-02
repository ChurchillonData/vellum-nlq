from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.resolve_schemas import QueryResolveResponse
from app.api.schemas import QueryExecuteResponse
from app.ask.examples import AskExample
from app.ask.service import AskResult


class AskRequest(BaseModel):
    """Question submitted to the product-facing ask endpoint."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    metric_id: str | None = Field(default=None, min_length=1)
    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = Field(default=None, min_length=1)
    group_by: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_date_range(self) -> "AskRequest":
        """Validate explicit dates while allowing the question parser to infer them."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date must be on or before end_date")
        return self


class AskResponse(QueryResolveResponse):
    """Ask endpoint response for answer, clarification, or blocked states."""

    query_id: str
    answer: QueryExecuteResponse | None = None

    @classmethod
    def from_ask_result(
        cls,
        result: AskResult,
        query_id: str | None = None,
    ) -> "AskResponse":
        """Convert an ask orchestration result into API JSON."""
        if query_id is None:
            raise ValueError("query_id is required for ask responses")

        resolution = QueryResolveResponse.from_resolution(result.resolution)
        answer = None

        if result.build_result is not None and result.execution_result is not None:
            answer = QueryExecuteResponse.from_execution_result(
                result.build_result,
                result.execution_result,
                query_id=query_id,
                planning_ms=result.planning_ms,
                execution_ms=result.execution_ms,
            )

        payload = resolution.model_dump()
        payload["status"] = result.status
        payload["query_id"] = query_id
        payload["answer"] = answer
        return cls(**payload)


class AskExampleResponse(AskRequest):
    """One golden ask example exposed to the frontend and tests."""

    id: str
    label: str
    expected_status: str

    @classmethod
    def from_example(cls, example: AskExample) -> "AskExampleResponse":
        """Convert an internal golden example into API JSON."""
        return cls(
            id=example.id,
            label=example.label,
            question=example.question,
            expected_status=example.expected_status,
            start_date=example.start_date,
            end_date=example.end_date,
            plan_tier=example.plan_tier,
            group_by=example.group_by,
        )


class AskExamplesResponse(BaseModel):
    """Golden ask examples grouped by expected UI state."""

    examples: list[AskExampleResponse]
