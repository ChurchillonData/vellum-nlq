from app.api.resolve_schemas import QueryResolveRequest, QueryResolveResponse
from app.api.schemas import QueryExecuteResponse
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
