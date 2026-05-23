from datetime import date

from app.analytics.models import AnalyticsRequest
from app.planner.decline_rate import build_decline_rate_plan
from app.planner.loss_ratio import build_loss_ratio_plan
from app.semantic.resolver import resolve_request


def test_loss_ratio_plan_uses_approved_supporting_joins(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="loss_ratio",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )
    resolved = resolve_request(health_uk_catalogue, request)

    plan = build_loss_ratio_plan(health_uk_catalogue, resolved)

    assert plan.tables == ("claims", "members", "plans", "premium")
    assert {(join.left_table, join.right_table) for join in plan.joins} == {
        ("claims", "members"),
        ("premium", "members"),
        ("members", "plans"),
    }
    assert plan.result_shape.columns == ("loss_ratio",)
    assert "plans.plan_tier = plan_tier" in plan.filters


def test_decline_rate_plan_uses_claim_line_path(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )
    resolved = resolve_request(health_uk_catalogue, request)

    plan = build_decline_rate_plan(health_uk_catalogue, resolved)

    assert plan.tables == ("claim_lines", "claims", "members", "plans")
    assert {(join.left_table, join.right_table) for join in plan.joins} == {
        ("claim_lines", "claims"),
        ("claims", "members"),
        ("members", "plans"),
    }
    assert plan.result_shape.columns == ("decline_rate",)
    assert "claim_lines.service_date between start_date and end_date" in plan.filters


def test_decline_rate_plan_groups_by_consultant_specialty(health_uk_catalogue) -> None:
    request = AnalyticsRequest(
        metric_id="decline_rate",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        group_by=("consultant_specialty",),
    )
    resolved = resolve_request(health_uk_catalogue, request)

    plan = build_decline_rate_plan(health_uk_catalogue, resolved)

    assert plan.group_by == ("consultant_specialty",)
    assert plan.tables == ("claim_lines", "claims", "members", "plans", "providers")
    assert ("claim_lines", "providers") in {
        (join.left_table, join.right_table) for join in plan.joins
    }
    assert plan.result_shape.columns == ("consultant_specialty", "decline_rate")
    assert plan.result_shape.grain == "consultant_specialty"
