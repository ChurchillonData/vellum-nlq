import re
from dataclasses import dataclass
from datetime import date


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


def parse_ask_fields(question: str) -> ParsedAskFields:
    """Infer supported dates and filters from an ask question."""
    start_date, end_date = _parse_date_range(question)
    plan_tier = _parse_plan_tier(question)
    return ParsedAskFields(
        start_date=start_date,
        end_date=end_date,
        plan_tier=plan_tier,
    )


def _parse_date_range(question: str) -> tuple[date | None, date | None]:
    quarter_range = _parse_quarter(question)
    if quarter_range != (None, None):
        return quarter_range

    return _parse_iso_date_range(question)


def _parse_quarter(question: str) -> tuple[date | None, date | None]:
    patterns = (
        r"\bq([1-4])\s+(\d{4})\b",
        r"\b(\d{4})\s+q([1-4])\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        first, second = match.groups()
        quarter = int(first if len(first) == 1 else second)
        year = int(second if len(first) == 1 else first)
        return _quarter_bounds(year, quarter)

    return None, None


def _quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    start_month = ((quarter - 1) * 3) + 1
    end_month = start_month + 2
    end_day = 31 if end_month in {3, 12} else 30
    return date(year, start_month, 1), date(year, end_month, end_day)


def _parse_iso_date_range(question: str) -> tuple[date | None, date | None]:
    matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", question)
    if len(matches) < 2:
        return None, None

    start_date = date.fromisoformat(matches[0])
    end_date = date.fromisoformat(matches[1])
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")
    return start_date, end_date


def _parse_plan_tier(question: str) -> str | None:
    normalized = question.casefold()
    for token, label in PLAN_TIERS.items():
        if re.search(rf"\b{token}\b", normalized):
            return label
    return None
