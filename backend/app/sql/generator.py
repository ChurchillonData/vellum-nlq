from sqlalchemy import Date, String, bindparam, func, select, true
from sqlalchemy.dialects import postgresql

from app.analytics.models import GeneratedQuery, LogicalPlan
from app.db.schema import claim_lines, claims, enrolment_months, members, plans, premium


def generate_loss_ratio_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned loss-ratio request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())
    excluded_status = bindparam("excluded_status", "void", type_=String())

    claims_source = claims.join(members, claims.c.member_id == members.c.id).join(
        plans, members.c.plan_id == plans.c.id
    )
    premium_source = premium.join(members, premium.c.member_id == members.c.id).join(
        plans, members.c.plan_id == plans.c.id
    )

    claims_filters = [
        claims.c.incurred_date.between(start_date, end_date),
        claims.c.status != excluded_status,
    ]
    premium_filters = [premium.c.coverage_month.between(start_date, end_date)]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        claims_filters.append(plans.c.plan_tier == plan_tier)
        premium_filters.append(plans.c.plan_tier == plan_tier)

    claim_totals = (
        select(
            claims.c.member_id.label("member_id"),
            func.sum(claims.c.net_incurred_amount).label("incurred_claims"),
        )
        .select_from(claims_source)
        .where(*claims_filters)
        .group_by(claims.c.member_id)
        .cte("claim_totals")
    )
    premium_totals = (
        select(
            premium.c.member_id.label("member_id"),
            func.sum(premium.c.earned_amount).label("earned_premium"),
        )
        .select_from(premium_source)
        .where(*premium_filters)
        .group_by(premium.c.member_id)
        .cte("premium_totals")
    )

    statement = select(
        (
            func.sum(claim_totals.c.incurred_claims)
            / func.nullif(func.sum(premium_totals.c.earned_premium), 0)
        ).label("loss_ratio")
    ).select_from(
        claim_totals.join(
            premium_totals,
            claim_totals.c.member_id == premium_totals.c.member_id,
        )
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return GeneratedQuery(sql=str(compiled), parameters=compiled.params)


def generate_paid_claims_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned paid-claims request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())

    source = (
        claim_lines.join(claims, claim_lines.c.claim_id == claims.c.id)
        .join(members, claims.c.member_id == members.c.id)
        .join(plans, members.c.plan_id == plans.c.id)
    )
    filters = [claim_lines.c.paid_date.between(start_date, end_date)]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        filters.append(plans.c.plan_tier == plan_tier)

    statement = (
        select(func.sum(claim_lines.c.net_paid_amount).label("paid_claims"))
        .select_from(source)
        .where(*filters)
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return GeneratedQuery(sql=str(compiled), parameters=compiled.params)


def generate_claim_frequency_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned claim-frequency request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())
    excluded_status = bindparam("excluded_status", "void", type_=String())

    claims_source = claims.join(members, claims.c.member_id == members.c.id).join(
        plans, members.c.plan_id == plans.c.id
    )
    enrolment_source = enrolment_months.join(
        members,
        enrolment_months.c.member_id == members.c.id,
    ).join(plans, members.c.plan_id == plans.c.id)

    claims_filters = [
        claims.c.incurred_date.between(start_date, end_date),
        claims.c.status != excluded_status,
    ]
    enrolment_filters = [enrolment_months.c.coverage_month.between(start_date, end_date)]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        claims_filters.append(plans.c.plan_tier == plan_tier)
        enrolment_filters.append(plans.c.plan_tier == plan_tier)

    claim_counts = (
        select(func.count(claims.c.id.distinct()).label("claim_count"))
        .select_from(claims_source)
        .where(*claims_filters)
        .cte("claim_counts")
    )
    member_months = (
        select(func.sum(enrolment_months.c.member_months).label("member_months"))
        .select_from(enrolment_source)
        .where(*enrolment_filters)
        .cte("member_months")
    )

    statement = select(
        (
            claim_counts.c.claim_count
            * 1000
            / func.nullif(member_months.c.member_months, 0)
        ).label("claim_frequency")
    ).select_from(claim_counts.join(member_months, true()))

    compiled = statement.compile(dialect=postgresql.dialect())
    return GeneratedQuery(sql=str(compiled), parameters=compiled.params)
