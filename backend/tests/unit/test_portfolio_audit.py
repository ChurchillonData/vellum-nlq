from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.portfolio.audit import (
    audit_generated_portfolio,
    expected_claim_count,
    metric_range_check,
)
from app.portfolio.live import LIVE_METRICS, _query_checks


def test_generated_portfolio_audit_validates_volume_and_distributions() -> None:
    report = audit_generated_portfolio(
        member_count=120,
        month_count=18,
        chunk_size=50,
    )

    assert report.passed is True
    assert report.summary.row_counts["claims"] == expected_claim_count(120)
    assert report.summary.generated_rows_per_second > 0
    assert {check.name for check in report.checks} >= {
        "volume:members",
        "volume:premium_rows",
        "metric:loss_ratio",
        "metric:claim_frequency",
        "metric:claim_severity",
        "metric:decline_rate",
    }


def test_generated_portfolio_audit_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        audit_generated_portfolio(member_count=0)


def test_metric_range_check_reports_out_of_range_value() -> None:
    check = metric_range_check("loss_ratio", Decimal("0.50"))

    assert check.passed is False
    assert check.observed == "0.500"
    assert check.expected == "0.780 to 0.920"


def test_live_query_checks_validate_metric_values_and_latency(monkeypatch) -> None:
    values = {
        "loss_ratio": Decimal("0.84"),
        "claim_frequency": Decimal("102"),
        "claim_severity": Decimal("2900"),
        "decline_rate": Decimal("0.07"),
    }
    clock = iter(value for pair in ((0.0, 0.1), (1.0, 1.1), (2.0, 2.1), (3.0, 3.1)) for value in pair)

    monkeypatch.setattr("app.portfolio.live.load_catalogue", lambda *_args: object())
    monkeypatch.setattr(
        "app.portfolio.live.build_query",
        lambda _catalogue, request: SimpleNamespace(
            provenance=SimpleNamespace(metric_id=request.metric_id)
        ),
    )
    monkeypatch.setattr(
        "app.portfolio.live.execute_postgres_query",
        lambda build_result, database_url: SimpleNamespace(
            rows=[
                {
                    build_result.provenance.metric_id: values[
                        build_result.provenance.metric_id
                    ]
                }
            ]
        ),
    )
    monkeypatch.setattr("app.portfolio.live.perf_counter", lambda: next(clock))

    checks = _query_checks(Settings(), max_latency_ms=200)

    assert len(checks) == len(LIVE_METRICS) * 2
    assert all(check.passed for check in checks)
