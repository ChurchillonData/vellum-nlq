import re
from dataclasses import dataclass
from datetime import date

from app.ask.period_parser import parse_period_range
from app.data_window import rolling_data_window


PLAN_TIERS = {
    "essential": "Essential",
    "comprehensive": "Comprehensive",
    "executive": "Executive",
}


@dataclass(frozen=True)
class ParsedAskFields:
    """Structured filters inferred from a natural-language question."""

    start_date: date | None = None
    end_date: date | None = None
    plan_tier: str | None = None
    group_by: tuple[str, ...] = ()


def parse_ask_fields(
    question: str,
    as_of_date: date | None = None,
    month_count: int = 18,
) -> ParsedAskFields:
    """Infer supported dates and filters from an ask question."""
    window = rolling_data_window(as_of_date=as_of_date, month_count=month_count)
    start_date, end_date = parse_period_range(question, window)
    plan_tier = _parse_plan_tier(question)
    group_by = _parse_group_by(question)
    return ParsedAskFields(
        start_date=start_date,
        end_date=end_date,
        plan_tier=plan_tier,
        group_by=group_by,
    )


def _parse_plan_tier(question: str) -> str | None:
    normalized = question.casefold()
    for token, label in PLAN_TIERS.items():
        if re.search(rf"\b{token}\b", normalized):
            return label
    return None


def _parse_group_by(question: str) -> tuple[str, ...]:
    normalized = question.casefold()
    plan_tier_patterns = (
        r"\bby\s+plan\s+tier\b",
        r"\bper\s+plan\s+tier\b",
        r"\bby\s+tier\b",
    )
    if any(re.search(pattern, normalized) for pattern in plan_tier_patterns):
        return ("plan_tier",)

    region_patterns = (
        r"\bby\s+member\s+region\b",
        r"\bby\s+region\b",
        r"\bper\s+region\b",
    )
    if any(re.search(pattern, normalized) for pattern in region_patterns):
        return ("region",)

    specialty_patterns = (
        r"\bby\s+consultant\s+specialty\b",
        r"\bby\s+specialty\b",
        r"\bper\s+consultant\s+specialty\b",
        r"\bper\s+specialty\b",
    )
    if any(re.search(pattern, normalized) for pattern in specialty_patterns):
        return ("consultant_specialty",)
    return ()
