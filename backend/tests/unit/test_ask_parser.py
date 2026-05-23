from datetime import date

import pytest

from app.ask.parser import parse_ask_fields


def test_parser_extracts_quarter_and_plan_tier() -> None:
    parsed = parse_ask_fields(
        "What was loss ratio for the Comprehensive plan tier in Q1 2026?"
    )

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)
    assert parsed.plan_tier == "Comprehensive"


def test_parser_extracts_year_first_quarter_format() -> None:
    parsed = parse_ask_fields("Show paid claims for executive members in 2026 Q2")

    assert parsed.start_date == date(2026, 4, 1)
    assert parsed.end_date == date(2026, 6, 30)
    assert parsed.plan_tier == "Executive"


def test_parser_extracts_iso_date_range() -> None:
    parsed = parse_ask_fields(
        "Show claim frequency from 2026-01-01 to 2026-03-31"
    )

    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 3, 31)


def test_parser_rejects_reversed_iso_date_range() -> None:
    with pytest.raises(ValueError, match="start_date must be on or before end_date"):
        parse_ask_fields("Show loss ratio from 2026-03-31 to 2026-01-01")
