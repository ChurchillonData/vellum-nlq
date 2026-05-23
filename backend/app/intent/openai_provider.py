from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.intent.models import IntentResult
from app.semantic.models import Catalogue


class OpenAIIntentPayload(BaseModel):
    """Structured output schema returned by OpenAI."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = None
    group_by: list[str] = Field(default_factory=list)
    confidence: float | None = None


class OpenAIIntentProvider:
    """Extract structured intent with OpenAI, never SQL."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OpenAI intent provider requires an API key")

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "OpenAI provider requires the optional 'openai' package."
            ) from error

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return a catalogue-shaped structured intent proposal."""
        payload = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": _system_prompt(catalogue),
                },
                {"role": "user", "content": question},
            ],
            text_format=OpenAIIntentPayload,
        ).output_parsed

        if payload is None:
            return IntentResult(source="openai")

        return IntentResult(
            metric_id=payload.metric_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            plan_tier=payload.plan_tier,
            group_by=tuple(payload.group_by),
            confidence=payload.confidence,
            source="openai",
        )


def _system_prompt(catalogue: Catalogue) -> str:
    metric_ids = ", ".join(sorted(catalogue.metrics))
    return (
        "Extract structured analytics intent for Vellum-NLQ. "
        "Return only fields in the schema. Do not write SQL. "
        "If a value is not present, return null or an empty list. "
        f"Allowed metric_id values: {metric_ids}. "
        "Allowed plan_tier values: Essential, Comprehensive, Executive. "
        "Allowed group_by values: consultant_specialty."
    )
