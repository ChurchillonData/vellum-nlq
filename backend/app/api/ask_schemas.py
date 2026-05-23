from pydantic import BaseModel

from app.api.resolve_schemas import QueryResolveRequest, QueryResolveResponse
from app.api.schemas import QueryExecuteResponse
from app.ask.examples import AskExample
from app.ask.service import AskResult


class AskRequest(QueryResolveRequest):
    """Question submitted to the product-facing ask endpoint."""


class AskResponse(QueryResolveResponse):
    """Ask endpoint response for answer, clarification, or blocked states."""

    answer: QueryExecuteResponse | None = None

    @classmethod
    def from_ask_result(
        cls,
        result: AskResult,
        query_id: str | None = None,
    ) -> "AskResponse":
        """Convert an ask orchestration result into API JSON."""
        resolution = QueryResolveResponse.from_resolution(result.resolution)
        answer = None

        if result.build_result is not None and result.execution_result is not None:
            if query_id is None:
                raise ValueError("query_id is required for answer responses")
            answer = QueryExecuteResponse.from_execution_result(
                result.build_result,
                result.execution_result,
                query_id=query_id,
            )

        payload = resolution.model_dump()
        payload["status"] = result.status
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
        )


class AskExamplesResponse(BaseModel):
    """Golden ask examples grouped by expected UI state."""

    examples: list[AskExampleResponse]
