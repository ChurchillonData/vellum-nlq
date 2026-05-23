from app.config import Settings
from app.intent.deterministic import DeterministicIntentProvider
from app.intent.models import IntentProvider
from app.intent.openai_provider import OpenAIIntentProvider


_override_provider: IntentProvider | None = None


def build_intent_provider(settings: Settings) -> IntentProvider:
    """Create the configured intent provider."""
    if _override_provider is not None:
        return _override_provider

    if settings.intent_provider == "openai":
        return OpenAIIntentProvider(
            api_key=settings.openai_api_key or "",
            model=settings.openai_model,
        )

    return DeterministicIntentProvider()


def set_intent_provider_override(provider: IntentProvider | None) -> None:
    """Override the provider in tests."""
    global _override_provider
    _override_provider = provider
