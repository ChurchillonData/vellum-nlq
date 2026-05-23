from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeFinding:
    """A deterministic product-scope rule triggered by a user question."""

    reason_id: str
    reason: str


FORECAST_WORDS = {
    "forecast",
    "forecasting",
    "predict",
    "prediction",
    "project",
    "projection",
    "next",
    "future",
}


def classify_question_scope(tokens: set[str]) -> ScopeFinding | None:
    """Return a scope finding for unsupported analytics intents."""
    if tokens & FORECAST_WORDS:
        return ScopeFinding(
            reason_id="forecasting_not_supported",
            reason="Forecasting questions are outside the current analytics scope.",
        )

    return None

