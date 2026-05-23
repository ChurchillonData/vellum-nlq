from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.intent.models import IntentProviderError, IntentResult
from app.semantic.models import Catalogue


ALLOWED_PLAN_TIERS = {"Essential", "Comprehensive", "Executive"}
ALLOWED_GROUP_BY = {"consultant_specialty"}


class OpenAIIntentPayload(BaseModel):
    """Structured output schema returned by OpenAI."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = None
    group_by: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


class OpenAIIntentProvider:
    """Extract structured intent with OpenAI, never SQL."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        min_confidence: float,
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key:
            raise ValueError("OpenAI intent provider requires an API key")

        if client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise RuntimeError(
                    "OpenAI provider requires the optional 'openai' package."
                ) from error

            client = OpenAI(
                api_key=api_key,
                timeout=timeout_seconds,
                max_retries=max_retries,
            )

        self.client = client
        self.model = model
        self.min_confidence = min_confidence

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return a catalogue-shaped structured intent proposal."""
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": _system_prompt(catalogue),
                    },
                    {"role": "user", "content": question},
                ],
                text_format=OpenAIIntentPayload,
            )
        except Exception as error:
            raise IntentProviderError("OpenAI intent extraction failed") from error

        payload = response.output_parsed

        if payload is None:
            return IntentResult(source="openai")

        return _payload_to_intent(
            catalogue=catalogue,
            payload=payload,
            min_confidence=self.min_confidence,
        )


def _payload_to_intent(
    catalogue: Catalogue,
    payload: OpenAIIntentPayload,
    min_confidence: float,
) -> IntentResult:
    """Validate provider output against the catalogue boundary."""
    if payload.confidence is not None and payload.confidence < min_confidence:
        return IntentResult(confidence=payload.confidence, source="openai")

    metric_id = payload.metric_id
    if metric_id not in catalogue.metrics:
        metric_id = None

    plan_tier = payload.plan_tier
    if plan_tier not in ALLOWED_PLAN_TIERS:
        plan_tier = None

    group_by = tuple(item for item in payload.group_by if item in ALLOWED_GROUP_BY)

    return IntentResult(
        metric_id=metric_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        plan_tier=plan_tier,
        group_by=group_by,
        confidence=payload.confidence,
        source="openai",
    )


def _system_prompt(catalogue: Catalogue) -> str:
    metric_lines = [
        (
            f"- {metric.id}: {metric.label}. "
            f"Synonyms: {', '.join(metric.synonyms) or 'none'}."
        )
        for metric in sorted(catalogue.metrics.values(), key=lambda item: item.id)
    ]
    return (
        "Extract structured analytics intent for Vellum-NLQ. "
        "Return only fields in the schema. Do not write SQL. "
        "If a value is not present, return null or an empty list. "
        "Use metric_id only when the question clearly maps to one of these "
        f"catalogue metrics:\n{chr(10).join(metric_lines)}\n"
        "Allowed plan_tier values: Essential, Comprehensive, Executive. "
        "Allowed group_by values: consultant_specialty."
    )
