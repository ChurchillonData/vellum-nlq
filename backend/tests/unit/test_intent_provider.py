import pytest
from pydantic import ValidationError

from app.intent.deterministic import DeterministicIntentProvider
from app.intent.factory import build_intent_provider
from app.intent.fallback import FallbackIntentProvider
from app.intent.models import IntentProviderError
from app.intent.openai_provider import OpenAIIntentPayload, OpenAIIntentProvider
from app.config import Settings


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


def test_openai_intent_payload_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        OpenAIIntentPayload.model_validate(
            {
                "metric_id": "loss_ratio",
                "confidence": 1.2,
            }
        )


def test_openai_provider_sanitizes_output_against_catalogue(
    health_uk_catalogue,
) -> None:
    client = _FakeOpenAIClient(
        OpenAIIntentPayload(
            metric_id="hallucinated_metric",
            start_date="2026-01-01",
            end_date="2026-03-31",
            plan_tier="Unknown tier",
            group_by=["consultant_specialty", "unknown_dimension"],
            confidence=0.95,
        )
    )
    provider = OpenAIIntentProvider(
        api_key="test",
        model="test-model",
        timeout_seconds=8,
        max_retries=1,
        min_confidence=0.70,
        client=client,
    )

    result = provider.extract_intent(health_uk_catalogue, "question")

    assert result.metric_id is None
    assert result.start_date.isoformat() == "2026-01-01"
    assert result.end_date.isoformat() == "2026-03-31"
    assert result.plan_tier is None
    assert result.group_by == ("consultant_specialty",)
    assert result.source == "openai"


def test_openai_provider_drops_low_confidence_metric(health_uk_catalogue) -> None:
    client = _FakeOpenAIClient(
        OpenAIIntentPayload(
            metric_id="loss_ratio",
            start_date="2026-01-01",
            end_date="2026-03-31",
            confidence=0.40,
        )
    )
    provider = OpenAIIntentProvider(
        api_key="test",
        model="test-model",
        timeout_seconds=8,
        max_retries=1,
        min_confidence=0.70,
        client=client,
    )

    result = provider.extract_intent(health_uk_catalogue, "question")

    assert result.metric_id is None
    assert result.start_date is None
    assert result.end_date is None
    assert result.confidence == 0.40


def test_openai_provider_wraps_client_errors(health_uk_catalogue) -> None:
    provider = OpenAIIntentProvider(
        api_key="test",
        model="test-model",
        timeout_seconds=8,
        max_retries=1,
        min_confidence=0.70,
        client=_FailingOpenAIClient(),
    )

    with pytest.raises(IntentProviderError):
        provider.extract_intent(health_uk_catalogue, "question")


def test_factory_falls_back_when_openai_is_not_configured() -> None:
    provider = build_intent_provider(
        Settings(intent_provider="openai", openai_api_key=None)
    )

    assert isinstance(provider, DeterministicIntentProvider)


def test_factory_wraps_openai_with_fallback_when_configured() -> None:
    provider = build_intent_provider(
        Settings(intent_provider="openai", openai_api_key="test")
    )

    assert isinstance(provider, FallbackIntentProvider)


class _FakeOpenAIResponse:
    def __init__(self, payload: OpenAIIntentPayload) -> None:
        self.output_parsed = payload


class _FakeResponses:
    def __init__(self, payload: OpenAIIntentPayload) -> None:
        self.payload = payload

    def parse(self, **kwargs):
        return _FakeOpenAIResponse(self.payload)


class _FakeOpenAIClient:
    def __init__(self, payload: OpenAIIntentPayload) -> None:
        self.responses = _FakeResponses(payload)


class _FailingResponses:
    def parse(self, **kwargs):
        raise RuntimeError("network unavailable")


class _FailingOpenAIClient:
    responses = _FailingResponses()
