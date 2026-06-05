import re
from datetime import date, timedelta

from app.data_window import DataWindow, add_months, latest_completed_quarter


MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

QUARTER_WORDS = {
    "first": 1,
    "1st": 1,
    "one": 1,
    "second": 2,
    "2nd": 2,
    "two": 2,
    "third": 3,
    "3rd": 3,
    "three": 3,
    "fourth": 4,
    "4th": 4,
    "four": 4,
}


def parse_period_range(
    question: str,
    window: DataWindow,
) -> tuple[date | None, date | None]:
    """Infer a supported date range from natural period wording."""
    for parser in (
        _parse_quarter,
        _parse_iso_date_range,
        _parse_natural_date_range,
        _parse_natural_day,
        _parse_natural_month,
        _parse_relative_range,
        _parse_year_range,
    ):
        start_date, end_date = parser(question, window)
        if start_date is not None and end_date is not None:
            return start_date, end_date

    return None, None


def _parse_quarter(
    question: str,
    window: DataWindow,
) -> tuple[date | None, date | None]:
    if re.search(r"\blast\s+quarter\b", question, flags=re.IGNORECASE):
        return latest_completed_quarter(window.as_of_date)

    patterns = (
        r"\bq([1-4])\s+(\d{4})\b",
        r"\b(\d{4})\s+q([1-4])\b",
        r"\b(?:quarter|q)\s*([1-4])\s+(?:of\s+)?(\d{4})\b",
        r"\b(?:first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\s+quarter\s+(?:of\s+)?(\d{4})\b",
        r"\b(\d{4})\s+(?:first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\s+quarter\b",
        r"\bq([1-4])\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        groups = match.groups()
        if len(groups) == 1:
            quarter = _quarter_number(match.group(0))
            year = (
                int(groups[0])
                if len(groups[0]) == 4
                else latest_completed_quarter(window.as_of_date)[0].year
            )
            return _quarter_bounds(year, quarter)

        first, second = groups
        if first.isdigit() and len(first) == 4:
            year = int(first)
            quarter = _quarter_number(match.group(0))
        elif second.isdigit() and len(second) == 4:
            year = int(second)
            quarter = _quarter_number(match.group(0))
        else:
            quarter = int(first if len(first) == 1 else second)
            year = int(second if len(first) == 1 else first)
        return _quarter_bounds(year, quarter)

    return None, None


def _parse_iso_date_range(
    question: str,
    _window: DataWindow,
) -> tuple[date | None, date | None]:
    matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", question)
    if not matches:
        return None, None

    start_date = _parse_iso_date(matches[0])
    end_date = _parse_iso_date(matches[1]) if len(matches) > 1 else start_date
    return _checked_range(start_date, end_date)


def _parse_natural_date_range(
    question: str,
    _window: DataWindow,
) -> tuple[date | None, date | None]:
    month_year_range = _parse_two_month_years(question)
    if month_year_range != (None, None):
        return month_year_range

    return _parse_months_with_shared_year(question)


def _parse_two_month_years(question: str) -> tuple[date | None, date | None]:
    month_pattern = _month_pattern()
    patterns = (
        rf"\b({month_pattern})\s+(\d{{4}})\s+(?:to|through|until|-)\s+({month_pattern})\s+(\d{{4}})\b",
        rf"\b(\d{{4}})\s+({month_pattern})\s+(?:to|through|until|-)\s+(\d{{4}})\s+({month_pattern})\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        groups = match.groups()
        if groups[0].isdigit():
            start_year = int(groups[0])
            start_month = _month_number(groups[1])
            end_year = int(groups[2])
            end_month = _month_number(groups[3])
        else:
            start_month = _month_number(groups[0])
            start_year = int(groups[1])
            end_month = _month_number(groups[2])
            end_year = int(groups[3])

        return _month_range_bounds(start_year, start_month, end_year, end_month)

    return None, None


def _parse_months_with_shared_year(question: str) -> tuple[date | None, date | None]:
    month_pattern = _month_pattern()
    pattern = (
        rf"\b({month_pattern})\s+(?:to|through|until|-)\s+"
        rf"({month_pattern})\s+(\d{{4}})\b"
    )
    match = re.search(pattern, question, flags=re.IGNORECASE)
    if match is None:
        return None, None

    start_month = _month_number(match.group(1))
    end_month = _month_number(match.group(2))
    year = int(match.group(3))
    return _month_range_bounds(year, start_month, year, end_month)


def _parse_natural_day(
    question: str,
    _window: DataWindow,
) -> tuple[date | None, date | None]:
    month_pattern = _month_pattern()
    patterns = (
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_pattern})\s+(\d{{4}})\b",
        rf"\b({month_pattern})\s+(\d{{1,2}})(?:st|nd|rd|th)?[,]?\s+(\d{{4}})\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        groups = match.groups()
        if groups[0].isdigit():
            day = int(groups[0])
            month = _month_number(groups[1])
            year = int(groups[2])
        else:
            month = _month_number(groups[0])
            day = int(groups[1])
            year = int(groups[2])
        value = _safe_date(year, month, day)
        return value, value

    return None, None


def _parse_natural_month(
    question: str,
    _window: DataWindow,
) -> tuple[date | None, date | None]:
    month_pattern = _month_pattern()
    patterns = (
        rf"\b({month_pattern})\s+(\d{{4}})\b",
        rf"\b(\d{{4}})\s+({month_pattern})\b",
    )

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match is None:
            continue

        first, second = match.groups()
        if first.isdigit():
            year = int(first)
            month = _month_number(second)
        else:
            month = _month_number(first)
            year = int(second)
        return _month_bounds(year, month)

    return None, None


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


def _parse_year_range(
    question: str,
    _window: DataWindow,
) -> tuple[date | None, date | None]:
    match = re.search(r"\b(?:in|for|during)\s+(20\d{2})\b", question, re.IGNORECASE)
    if match is None:
        return None, None

    year = int(match.group(1))
    return date(year, 1, 1), date(year, 12, 31)


def _quarter_number(value: str) -> int:
    normalized = value.casefold()
    digit_match = re.search(r"\b[1-4]\b|q([1-4])", normalized)
    if digit_match is not None:
        return int(digit_match.group(1) or digit_match.group(0))

    for word, quarter in QUARTER_WORDS.items():
        if re.search(rf"\b{word}\b", normalized):
            return quarter

    raise ValueError("unsupported quarter phrase")


def _quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    start_month = ((quarter - 1) * 3) + 1
    end_month = start_month + 2
    end_day = 31 if end_month in {3, 12} else 30
    return date(year, start_month, 1), date(year, end_month, end_day)


def _month_range_bounds(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> tuple[date, date]:
    start_date = date(start_year, start_month, 1)
    end_date = _month_bounds(end_year, end_month)[1]
    return _checked_range(start_date, end_date)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start_date = date(year, month, 1)
    next_month = add_months(start_date, 1)
    return start_date, next_month - timedelta(days=1)


def _checked_range(start_date: date, end_date: date) -> tuple[date, date]:
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")
    return start_date, end_date


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("invalid date in question") from error


def _safe_date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as error:
        raise ValueError("invalid date in question") from error


def _month_number(value: str) -> int:
    return MONTHS[value.casefold()]


def _month_pattern() -> str:
    return "|".join(sorted(MONTHS, key=len, reverse=True))
