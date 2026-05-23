from app.intent.models import IntentResult
from app.semantic.models import Catalogue


class FakeIntentProvider:
    """Test provider that returns a fixed structured intent."""

    def __init__(self, result: IntentResult) -> None:
        self.result = result

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return the configured intent without reading the question."""
        return self.result
