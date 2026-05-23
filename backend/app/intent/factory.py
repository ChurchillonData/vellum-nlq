from app.config import Settings
from app.intent.deterministic import DeterministicIntentProvider
from app.intent.fallback import FallbackIntentProvider
from app.intent.models import IntentProvider, IntentProviderError
from app.intent.openai_provider import OpenAIIntentProvider


_override_provider: IntentProvider | None = None


def build_intent_provider(settings: Settings) -> IntentProvider:
    """Create the configured intent provider."""
    if _override_provider is not None:
        return _override_provider

    if settings.intent_provider == "openai":
        fallback = DeterministicIntentProvider()
        try:
            primary = OpenAIIntentProvider(
                api_key=settings.openai_api_key or "",
                model=settings.openai_model,
                timeout_seconds=settings.openai_timeout_seconds,
                max_retries=settings.openai_max_retries,
                min_confidence=settings.openai_min_confidence,
            )
        except (RuntimeError, ValueError):
            if settings.openai_fallback_enabled:
                return fallback
            raise IntentProviderError("OpenAI intent provider is unavailable")

        return FallbackIntentProvider(
            primary=primary,
            fallback=fallback,
            fallback_enabled=settings.openai_fallback_enabled,
        )

    return DeterministicIntentProvider()


def set_intent_provider_override(provider: IntentProvider | None) -> None:
    """Override the provider in tests."""
    global _override_provider
    _override_provider = provider
