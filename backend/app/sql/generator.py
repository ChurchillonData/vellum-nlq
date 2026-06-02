from sqlalchemy import Date, Integer, Numeric, String, bindparam, cast, func, select, true
from sqlalchemy.dialects import postgresql

from app.analytics.models import GeneratedQuery, LogicalPlan
from app.db.schema import (
    claim_lines,
    claims,
    enrolment_months,
    members,
    plans,
    premium,
    providers,
)


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

    group_key = _group_key(plan)
    group_expression = _member_group_expression(group_key)

    claim_columns = [func.sum(claims.c.net_incurred_amount).label("incurred_claims")]
    premium_columns = [func.sum(premium.c.earned_amount).label("earned_premium")]
    if group_expression is not None:
        claim_columns.insert(0, group_expression.label(group_key))
        premium_columns.insert(0, group_expression.label(group_key))
    else:
        claim_columns.insert(0, claims.c.member_id.label("member_id"))
        premium_columns.insert(0, premium.c.member_id.label("member_id"))

    claim_totals_query = (
        select(*claim_columns)
        .select_from(claims_source)
        .where(*claims_filters)
    )
    premium_totals_query = (
        select(*premium_columns)
        .select_from(premium_source)
        .where(*premium_filters)
    )

    if group_expression is not None:
        claim_totals_query = claim_totals_query.group_by(group_expression)
        premium_totals_query = premium_totals_query.group_by(group_expression)
    else:
        claim_totals_query = claim_totals_query.group_by(claims.c.member_id)
        premium_totals_query = premium_totals_query.group_by(premium.c.member_id)

    claim_totals = claim_totals_query.cte("claim_totals")
    premium_totals = premium_totals_query.cte("premium_totals")
    loss_ratio = (
        func.sum(claim_totals.c.incurred_claims)
        / func.nullif(func.sum(premium_totals.c.earned_premium), 0)
    ).label("loss_ratio")

    if group_key is not None:
        join_condition = claim_totals.c[group_key] == premium_totals.c[group_key]
    else:
        join_condition = claim_totals.c.member_id == premium_totals.c.member_id

    source = claim_totals.join(premium_totals, join_condition)
    if group_key is None:
        statement = select(loss_ratio).select_from(source)
    else:
        statement = (
            select(claim_totals.c[group_key], loss_ratio)
            .select_from(source)
            .group_by(claim_totals.c[group_key])
            .order_by(loss_ratio.element.desc())
            .limit(_result_limit(plan))
        )

    compiled = statement.compile(dialect=postgresql.dialect())
    compact_compiled = _compact_loss_ratio_statement(
        plan=plan,
        claim_totals_query=claim_totals_query,
        premium_totals_query=premium_totals_query,
    ).compile(dialect=postgresql.dialect())
    return GeneratedQuery(
        sql=str(compiled),
        compact_sql=str(compact_compiled),
        parameters=compiled.params,
    )


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

    paid_claims = func.sum(claim_lines.c.net_paid_amount).label("paid_claims")
    statement = _aggregate_statement(
        plan=plan,
        source=source,
        filters=filters,
        metric_column=paid_claims,
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return _generated_query(compiled)


def generate_incurred_claims_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned incurred-claims request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())
    excluded_status = bindparam("excluded_status", "void", type_=String())

    source = claims.join(members, claims.c.member_id == members.c.id).join(
        plans, members.c.plan_id == plans.c.id
    )
    filters = [
        claims.c.incurred_date.between(start_date, end_date),
        claims.c.status != excluded_status,
    ]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        filters.append(plans.c.plan_tier == plan_tier)

    incurred_claims = func.sum(claims.c.net_incurred_amount).label("incurred_claims")
    statement = _aggregate_statement(
        plan=plan,
        source=source,
        filters=filters,
        metric_column=incurred_claims,
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return _generated_query(compiled)


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

    group_key = _group_key(plan)
    group_expression = _member_group_expression(group_key)

    claim_columns = [func.count(claims.c.id.distinct()).label("claim_count")]
    member_month_columns = [func.sum(enrolment_months.c.member_months).label("member_months")]
    if group_expression is not None:
        claim_columns.insert(0, group_expression.label(group_key))
        member_month_columns.insert(0, group_expression.label(group_key))

    claim_counts_query = (
        select(*claim_columns)
        .select_from(claims_source)
        .where(*claims_filters)
    )
    member_months_query = (
        select(*member_month_columns)
        .select_from(enrolment_source)
        .where(*enrolment_filters)
    )

    if group_expression is not None:
        claim_counts_query = claim_counts_query.group_by(group_expression)
        member_months_query = member_months_query.group_by(group_expression)

    claim_counts = claim_counts_query.cte("claim_counts")
    member_months = member_months_query.cte("member_months")
    claim_frequency = (
        claim_counts.c.claim_count
        * 1000
        / func.nullif(member_months.c.member_months, 0)
    ).label("claim_frequency")

    source = claim_counts.join(member_months, true())
    if group_key is not None:
        source = claim_counts.join(
            member_months,
            claim_counts.c[group_key] == member_months.c[group_key],
        )
        statement = (
            select(claim_counts.c[group_key], claim_frequency)
            .select_from(source)
            .order_by(claim_frequency.desc())
            .limit(_result_limit(plan))
        )
    else:
        statement = select(claim_frequency).select_from(source)

    compiled = statement.compile(dialect=postgresql.dialect())
    return _generated_query(compiled)


def generate_claim_severity_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned claim-severity request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())
    closed_status = bindparam("closed_status", "closed", type_=String())

    source = (
        claim_lines.join(claims, claim_lines.c.claim_id == claims.c.id)
        .join(members, claims.c.member_id == members.c.id)
        .join(plans, members.c.plan_id == plans.c.id)
    )
    filters = [
        claim_lines.c.paid_date.between(start_date, end_date),
        claims.c.status == closed_status,
    ]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        filters.append(plans.c.plan_tier == plan_tier)

    claim_severity = (
        func.sum(claim_lines.c.net_paid_amount)
        / func.nullif(func.count(claims.c.id.distinct()), 0)
    ).label("claim_severity")
    statement = _aggregate_statement(
        plan=plan,
        source=source,
        filters=filters,
        metric_column=claim_severity,
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return _generated_query(compiled)


def generate_decline_rate_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate parameterised SQL for a planned decline-rate request."""
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())

    source = (
        claim_lines.join(claims, claim_lines.c.claim_id == claims.c.id)
        .join(members, claims.c.member_id == members.c.id)
        .join(plans, members.c.plan_id == plans.c.id)
    )
    if plan.group_by == ("consultant_specialty",):
        source = source.join(providers, claim_lines.c.provider_id == providers.c.id)

    filters = [claim_lines.c.service_date.between(start_date, end_date)]

    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        filters.append(plans.c.plan_tier == plan_tier)

    declined_line_flag = cast(claim_lines.c.declined_amount > 0, Integer())
    decline_rate = (
        cast(func.sum(declined_line_flag), Numeric(12, 6))
        / func.nullif(func.count(claim_lines.c.id), 0)
    ).label("decline_rate")

    statement = _aggregate_statement(
        plan=plan,
        source=source,
        filters=filters,
        metric_column=decline_rate,
    )

    compiled = statement.compile(dialect=postgresql.dialect())
    return _generated_query(compiled)


def _generated_query(compiled) -> GeneratedQuery:
    """Return a generated query when compact SQL matches the full SQL."""
    sql = str(compiled)
    return GeneratedQuery(sql=sql, compact_sql=sql, parameters=compiled.params)


def _compact_loss_ratio_statement(
    plan: LogicalPlan,
    claim_totals_query,
    premium_totals_query,
):
    """Build a shorter loss-ratio statement with the same aggregation grain."""
    group_key = _group_key(plan)
    claim_totals = claim_totals_query.subquery("claim_totals")
    premium_totals = premium_totals_query.subquery("premium_totals")

    loss_ratio = (
        func.sum(claim_totals.c.incurred_claims)
        / func.nullif(func.sum(premium_totals.c.earned_premium), 0)
    ).label("loss_ratio")

    if group_key is None:
        source = claim_totals.join(
            premium_totals,
            claim_totals.c.member_id == premium_totals.c.member_id,
        )
        return select(loss_ratio).select_from(source)

    source = claim_totals.join(
        premium_totals,
        claim_totals.c[group_key] == premium_totals.c[group_key],
    )
    return (
        select(claim_totals.c[group_key], loss_ratio)
        .select_from(source)
        .group_by(claim_totals.c[group_key])
        .order_by(loss_ratio.element.desc())
        .limit(_result_limit(plan))
    )


def _aggregate_statement(plan: LogicalPlan, source, filters, metric_column):
    group_key = _group_key(plan)
    group_expression = _group_expression(group_key)
    if group_expression is None:
        return select(metric_column).select_from(source).where(*filters)

    return (
        select(group_expression.label(group_key), metric_column)
        .select_from(source)
        .where(*filters)
        .group_by(group_expression)
        .order_by(metric_column.element.desc())
        .limit(_result_limit(plan))
    )


def _group_key(plan: LogicalPlan) -> str | None:
    return plan.group_by[0] if plan.group_by else None


def _group_expression(group_key: str | None):
    if group_key == "consultant_specialty":
        return providers.c.specialty
    return _member_group_expression(group_key)


def _member_group_expression(group_key: str | None):
    if group_key == "plan_tier":
        return plans.c.plan_tier
    if group_key == "region":
        return members.c.region
    return None


def _result_limit(plan: LogicalPlan):
    return bindparam("result_limit", plan.result_shape.max_rows, type_=Integer())
