from datetime import date

import pytest

from app.ask.parser import parse_ask_fields
from app.data_window import rolling_data_window


AS_OF_DATE = date(2026, 6, 5)


def test_parser_extracts_quarter_and_plan_tier() -> None:
    parsed = parse_ask_fields(
        "What was loss ratio for the Comprehensive plan tier in Q1 2026?",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)
    assert parsed.plan_tier == "Comprehensive"


def test_parser_extracts_year_first_quarter_format() -> None:
    parsed = parse_ask_fields(
        "Show paid claims for executive members in 2026 Q2",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.start_date == date(2026, 4, 1)
    assert parsed.end_date == date(2026, 6, 30)
    assert parsed.plan_tier == "Executive"


@pytest.mark.parametrize(
    ("question", "expected_start", "expected_end"),
    [
        ("Show loss ratio for first quarter 2025", date(2025, 1, 1), date(2025, 3, 31)),
        ("Show loss ratio for quarter 1 2025", date(2025, 1, 1), date(2025, 3, 31)),
        ("Show loss ratio for 2025 first quarter", date(2025, 1, 1), date(2025, 3, 31)),
        ("Show loss ratio for 2025 Q1", date(2025, 1, 1), date(2025, 3, 31)),
    ],
)
def test_parser_extracts_quarter_word_variants(
    question: str,
    expected_start: date,
    expected_end: date,
) -> None:
    parsed = parse_ask_fields(question, as_of_date=AS_OF_DATE)

    assert parsed.start_date == expected_start
    assert parsed.end_date == expected_end


def test_parser_extracts_iso_date_range() -> None:
    parsed = parse_ask_fields(
        "Show claim frequency from 2026-01-01 to 2026-03-31",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)


def test_parser_extracts_single_iso_date() -> None:
    parsed = parse_ask_fields("Show claim count on 2026-05-14", as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2026, 5, 14)
    assert parsed.end_date == date(2026, 5, 14)


@pytest.mark.parametrize(
    "question",
    [
        "Show paid claims on 14 May 2026",
        "Show paid claims on 14th May 2026",
        "Show paid claims on May 14 2026",
        "Show paid claims on May 14, 2026",
    ],
)
def test_parser_extracts_natural_single_day(question: str) -> None:
    parsed = parse_ask_fields(question, as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2026, 5, 14)
    assert parsed.end_date == date(2026, 5, 14)


@pytest.mark.parametrize(
    "question",
    [
        "Show loss ratio for May 2026",
        "Show loss ratio for 2026 May",
    ],
)
def test_parser_extracts_month_name_year_variants(question: str) -> None:
    parsed = parse_ask_fields(question, as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2026, 5, 1)
    assert parsed.end_date == date(2026, 5, 31)


@pytest.mark.parametrize(
    ("question", "expected_start", "expected_end"),
    [
        ("Show paid claims from May to July 2025", date(2025, 5, 1), date(2025, 7, 31)),
        ("Show paid claims from May 2025 to July 2025", date(2025, 5, 1), date(2025, 7, 31)),
        ("Show paid claims from 2025 May to 2025 July", date(2025, 5, 1), date(2025, 7, 31)),
        ("Show paid claims from January 2026 to March 2026", date(2026, 1, 1), date(2026, 3, 31)),
    ],
)
def test_parser_extracts_month_range_variants(
    question: str,
    expected_start: date,
    expected_end: date,
) -> None:
    parsed = parse_ask_fields(question, as_of_date=AS_OF_DATE)

    assert parsed.start_date == expected_start
    assert parsed.end_date == expected_end


def test_parser_extracts_consultant_specialty_grouping() -> None:
    parsed = parse_ask_fields(
        "Show decline rate by consultant specialty for Comprehensive in Q1 2026",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.group_by == ("consultant_specialty",)
    assert parsed.plan_tier == "Comprehensive"
    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)


def test_parser_extracts_plan_tier_grouping_without_filter() -> None:
    parsed = parse_ask_fields(
        "Show loss ratio by plan tier in Q1 2026",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.group_by == ("plan_tier",)
    assert parsed.plan_tier is None
    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)


def test_parser_extracts_region_grouping_and_relative_period() -> None:
    parsed = parse_ask_fields(
        "Show paid claims by region for the last six months",
        as_of_date=AS_OF_DATE,
    )

    assert parsed.group_by == ("region",)
    assert parsed.start_date == date(2025, 12, 1)
    assert parsed.end_date == date(2026, 5, 31)


def test_parser_extracts_year_to_date() -> None:
    parsed = parse_ask_fields("Show claim frequency year to date", as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 5, 31)


def test_parser_extracts_latest_completed_quarter() -> None:
    parsed = parse_ask_fields("Show loss ratio last quarter", as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)


def test_parser_extracts_full_year_range() -> None:
    parsed = parse_ask_fields("Show incurred claims for 2025", as_of_date=AS_OF_DATE)

    assert parsed.start_date == date(2025, 1, 1)
    assert parsed.end_date == date(2025, 12, 31)


def test_parser_rejects_reversed_iso_date_range() -> None:
    with pytest.raises(ValueError, match="start_date must be on or before end_date"):
        parse_ask_fields(
            "Show loss ratio from 2026-03-31 to 2026-01-01",
            as_of_date=AS_OF_DATE,
        )


def test_parser_rejects_reversed_month_range() -> None:
    with pytest.raises(ValueError, match="start_date must be on or before end_date"):
        parse_ask_fields("Show loss ratio from July to May 2025", as_of_date=AS_OF_DATE)


def test_rolling_data_window_uses_completed_months() -> None:
    window = rolling_data_window(as_of_date=AS_OF_DATE, month_count=18)

    assert window.start_date == date(2024, 12, 1)
    assert window.end_date == date(2026, 5, 31)
