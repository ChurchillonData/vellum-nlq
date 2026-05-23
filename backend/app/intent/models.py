from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.semantic.models import Catalogue


@dataclass(frozen=True)
class IntentResult:
    """Structured intent proposed by an extraction provider."""

    metric_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = None
    group_by: tuple[str, ...] = ()
    confidence: float | None = None
    source: str = "deterministic"


class IntentProvider(Protocol):
    """Extract structured intent without generating SQL."""

    def extract_intent(self, catalogue: Catalogue, question: str) -> IntentResult:
        """Return catalogue-shaped intent for one user question."""
        ...


class IntentProviderError(RuntimeError):
    """Raised when an intent provider cannot return a usable response."""
