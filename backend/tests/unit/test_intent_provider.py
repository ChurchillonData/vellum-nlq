import pytest
from pydantic import ValidationError

from app.intent.deterministic import DeterministicIntentProvider
from app.intent.openai_provider import OpenAIIntentPayload


def test_deterministic_provider_extracts_supported_filters(health_uk_catalogue) -> None:
    provider = DeterministicIntentProvider()

    result = provider.extract_intent(
        health_uk_catalogue,
        "What was loss ratio by consultant specialty for Comprehensive in Q1 2026?",
    )

    assert result.metric_id is None
    assert result.start_date.isoformat() == "2026-01-01"
    assert result.end_date.isoformat() == "2026-03-31"
    assert result.plan_tier == "Comprehensive"
    assert result.group_by == ("consultant_specialty",)


def test_openai_intent_payload_does_not_accept_sql() -> None:
    with pytest.raises(ValidationError):
        OpenAIIntentPayload.model_validate(
            {
                "metric_id": "loss_ratio",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "plan_tier": "Comprehensive",
                "group_by": [],
                "confidence": 0.9,
                "sql": "DROP TABLE claims",
            }
        )
