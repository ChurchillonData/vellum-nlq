from datetime import date

from app.semantic.question_resolver import resolve_question


def test_question_resolver_resolves_direct_loss_ratio_question(health_uk_catalogue) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show incurred loss ratio for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "loss_ratio"
    assert result.resolved_request.plan_tier == "Comprehensive"
    assert result.candidates[0].confidence >= 0.70


def test_question_resolver_resolves_direct_paid_claims_question(health_uk_catalogue) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show paid claims for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "paid_claims"


def test_question_resolver_returns_clarification_for_claims_numbers(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="How are the claims numbers looking?",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    )

    assert result.status == "clarification_required"
    assert result.resolved_request is None
    assert [candidate.metric_id for candidate in result.candidates] == [
        "loss_ratio",
        "paid_claims",
        "claim_frequency",
    ]
    assert all(candidate.confidence == 0.42 for candidate in result.candidates)


def test_question_resolver_returns_unresolved_for_unknown_question(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show broker commission quality",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    )

    assert result.status == "unresolved"
    assert result.candidates == ()
    assert result.resolved_request is None


def test_question_resolver_blocks_destructive_database_intent(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Drop all claims from the database",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    )

    assert result.status == "blocked"
    assert result.candidates == ()
    assert result.resolved_request is None
    assert result.safety is not None
    assert result.safety.rule_id == "DDL_DROP_PATTERN"
    assert result.safety.severity == "critical"
