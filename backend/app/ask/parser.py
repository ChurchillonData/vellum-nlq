import re
from dataclasses import dataclass
from datetime import date

from app.data_window import (
    DataWindow,
    add_months,
    latest_completed_quarter,
    rolling_data_window,
)

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
    start_date, end_date = _parse_date_range(question, window)
    plan_tier = _parse_plan_tier(question)
    group_by = _parse_group_by(question)
    return ParsedAskFields(
        start_date=start_date,
        end_date=end_date,
        plan_tier=plan_tier,
        group_by=group_by,
    )


def _parse_date_range(
    question: str,
    window: DataWindow,
) -> tuple[date | None, date | None]:
    quarter_range = _parse_quarter(question, window)
    if quarter_range != (None, None):
        return quarter_range

    iso_range = _parse_iso_date_range(question)
    if iso_range != (None, None):
        return iso_range

    relative_range = _parse_relative_range(question, window)
    if relative_range != (None, None):
        return relative_range

    return _parse_year_range(question)


def _parse_quarter(
    question: str,
    window: DataWindow,
) -> tuple[date | None, date | None]:
    if re.search(r"\blast\s+quarter\b", question, flags=re.IGNORECASE):
        return latest_completed_quarter(window.as_of_date)

    patterns = (
        r"\bq([1-4])\s+(\d{4})\b",
        r"\b(\d{4})\s+q([1-4])\b",
        r"\bq([1-4])\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        groups = match.groups()
        if len(groups) == 1:
            quarter = int(groups[0])
            year = latest_completed_quarter(window.as_of_date)[0].year
            return _quarter_bounds(year, quarter)

        first, second = groups
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


def _parse_relative_range(
    question: str,
    window: DataWindow,
) -> tuple[date | None, date | None]:
    normalized = question.casefold()
    latest_month_start = date(window.end_date.year, window.end_date.month, 1)

    if re.search(r"\blast\s+(six|6)\s+months\b", normalized):
        start_date = add_months(latest_month_start, -5)
        return start_date, window.end_date

    if re.search(r"\blast\s+month\b", normalized):
        return latest_month_start, window.end_date

    if re.search(r"\b(this\s+year|year\s+to\s+date|ytd)\b", normalized):
        return date(window.as_of_date.year, 1, 1), window.end_date

    return None, None


def _parse_year_range(question: str) -> tuple[date | None, date | None]:
    match = re.search(r"\b(?:in|for|during)\s+(20\d{2})\b", question, re.IGNORECASE)
    if match is None:
        return None, None

    year = int(match.group(1))
    return date(year, 1, 1), date(year, 12, 31)


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
