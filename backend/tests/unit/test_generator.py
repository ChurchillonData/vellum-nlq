from datetime import date

from app.analytics.build import build_query
from app.analytics.models import AnalyticsRequest


def test_loss_ratio_query_is_parameterised_and_has_provenance(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    result = build_query(health_uk_catalogue, request)

    assert "WITH claim_totals AS" in result.query.sql
    assert "premium_totals AS" in result.query.sql
    assert "%(start_date)s" in result.query.sql
    assert "%(plan_tier)s" in result.query.sql
    assert "2026-01-01" not in result.query.sql
    assert "Comprehensive" not in result.query.sql
    assert result.query.parameters["start_date"] == date(2026, 1, 1)
    assert result.query.parameters["end_date"] == date(2026, 3, 31)
    assert result.query.parameters["plan_tier"] == "Comprehensive"

    assert result.provenance.metric_id == "loss_ratio"
    assert result.provenance.formula.startswith("SUM(claims.net_incurred_amount)")
    assert result.provenance.tables_used == ("claims", "members", "plans", "premium")
    assert result.provenance.result_shape.grain == "single_metric"
