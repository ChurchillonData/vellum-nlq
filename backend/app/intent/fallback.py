from app.intent.models import IntentProvider, IntentProviderError, IntentResult
from app.semantic.models import Catalogue


class FallbackIntentProvider:
    """Use a fallback provider when the primary provider is unavailable."""

    def __init__(
        self,
        primary: IntentProvider,
        fallback: IntentProvider,
        fallback_enabled: bool,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.fallback_enabled = fallback_enabled

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return primary intent, or fallback intent after provider failure."""
        try:
            return self.primary.extract_intent(catalogue, question)
        except IntentProviderError:
            if not self.fallback_enabled:
                raise
            return self.fallback.extract_intent(catalogue, question)
