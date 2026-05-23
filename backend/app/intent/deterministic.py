from app.ask.parser import parse_ask_fields
from app.intent.models import IntentResult
from app.semantic.models import Catalogue


class DeterministicIntentProvider:
    """Use local parsing only; this is the default provider."""

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return locally parsed filters without proposing a metric."""
        parsed = parse_ask_fields(question)
        return IntentResult(
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            plan_tier=parsed.plan_tier,
            group_by=parsed.group_by,
            source="deterministic",
        )
