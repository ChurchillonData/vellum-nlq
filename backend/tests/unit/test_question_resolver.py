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


def test_question_resolver_resolves_direct_claim_frequency_question(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show claim frequency for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "claim_frequency"


def test_question_resolver_resolves_direct_decline_rate_question(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show decline rate for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "decline_rate"


def test_question_resolver_resolves_direct_incurred_claims_question(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show incurred claims for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "incurred_claims"


def test_question_resolver_resolves_direct_claim_severity_question(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="Show claim severity for Q1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        plan_tier="Comprehensive",
    )

    assert result.status == "resolved"
    assert result.resolved_request is not None
    assert result.resolved_request.metric_id == "claim_severity"


def test_question_resolver_resolves_expanded_governed_metric_questions(
    health_uk_catalogue,
) -> None:
    questions = {
        "Show claim count for Q1": "claim_count",
        "Show covered members for Q1": "covered_members",
        "Show open claim rate for Q4 2025": "open_claim_rate",
        "Show out of network rate for Q1": "out_of_network_rate",
        "Show premium per member for Q1": "premium_per_member",
        "Show case reserves for Q4 2025": "case_reserves",
    }

    for question, metric_id in questions.items():
        result = resolve_question(
            health_uk_catalogue,
            question=question,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        )

        assert result.status == "resolved"
        assert result.resolved_request is not None
        assert result.resolved_request.metric_id == metric_id


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


def test_question_resolver_returns_out_of_scope_for_forecast(
    health_uk_catalogue,
) -> None:
    result = resolve_question(
        health_uk_catalogue,
        question="What will loss ratio be next quarter?",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
    )

    assert result.status == "out_of_scope"
    assert result.candidates == ()
    assert result.resolved_request is None
    assert result.scope is not None
    assert result.scope.reason_id == "forecasting_not_supported"


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
