from datetime import date

from app.ask.parser import parse_ask_fields
from app.intent.models import IntentResult
from app.semantic.models import Catalogue


class DeterministicIntentProvider:
    """Use local parsing only; this is the default provider."""

    def __init__(self, as_of_date: date | None = None, month_count: int = 18) -> None:
        self.as_of_date = as_of_date
        self.month_count = month_count

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return locally parsed filters without proposing a metric."""
        parsed = parse_ask_fields(
            question,
            as_of_date=self.as_of_date,
            month_count=self.month_count,
        )
        return IntentResult(
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            plan_tier=parsed.plan_tier,
            group_by=parsed.group_by,
            source="deterministic",
        )
