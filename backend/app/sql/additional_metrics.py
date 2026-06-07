from sqlalchemy import Date, Integer, Numeric, String, bindparam, cast, func, select
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
    reserves,
)


def generate_additional_metric_query(plan: LogicalPlan) -> GeneratedQuery:
    """Generate guarded SQL for one additional governed aggregate metric."""
    metric_id = plan.metric.id
    start_date = bindparam("start_date", plan.start_date, type_=Date())
    end_date = bindparam("end_date", plan.end_date, type_=Date())
    source, date_column = _source_and_date_column(metric_id)
    filters = [date_column.between(start_date, end_date)]

    if metric_id == "claim_count":
        excluded_status = bindparam("excluded_status", "void", type_=String())
        filters.append(claims.c.status != excluded_status)

    metric_column = _metric_column(metric_id)
    if plan.plan_tier:
        plan_tier = bindparam("plan_tier", plan.plan_tier, type_=String())
        filters.append(plans.c.plan_tier == plan_tier)

    statement = _aggregate_statement(plan, source, filters, metric_column, date_column)
    compiled = statement.compile(dialect=postgresql.dialect())
    return GeneratedQuery(
        sql=str(compiled),
        compact_sql=_compact_sql(plan),
        parameters=compiled.params,
    )


def _source_and_date_column(metric_id: str):
    member_claims = claims.join(members, claims.c.member_id == members.c.id).join(
        plans, members.c.plan_id == plans.c.id
    )
    definitions = {
        "claim_count": (member_claims, claims.c.incurred_date),
        "covered_members": (
            enrolment_months.join(
                members, enrolment_months.c.member_id == members.c.id
            ).join(plans, members.c.plan_id == plans.c.id),
            enrolment_months.c.coverage_month,
        ),
        "open_claim_rate": (member_claims, claims.c.incurred_date),
        "out_of_network_rate": (
            claim_lines.join(claims, claim_lines.c.claim_id == claims.c.id)
            .join(members, claims.c.member_id == members.c.id)
            .join(plans, members.c.plan_id == plans.c.id)
            .join(providers, claim_lines.c.provider_id == providers.c.id),
            claim_lines.c.service_date,
        ),
        "premium_per_member": (
            premium.join(members, premium.c.member_id == members.c.id).join(
                plans, members.c.plan_id == plans.c.id
            ),
            premium.c.coverage_month,
        ),
        "case_reserves": (
            reserves.join(claims, reserves.c.claim_id == claims.c.id)
            .join(members, claims.c.member_id == members.c.id)
            .join(plans, members.c.plan_id == plans.c.id),
            reserves.c.snapshot_date,
        ),
    }
    return definitions[metric_id]


def _metric_column(metric_id: str):
    if metric_id == "claim_count":
        return func.count(claims.c.id.distinct()).label(metric_id)
    if metric_id == "covered_members":
        return func.count(enrolment_months.c.member_id.distinct()).label(metric_id)
    if metric_id == "open_claim_rate":
        open_status = bindparam("open_status", "open", type_=String())
        return (
            cast(func.sum(cast(claims.c.status == open_status, Integer())), Numeric(12, 6))
            / func.nullif(func.count(claims.c.id), 0)
        ).label(metric_id)
    if metric_id == "out_of_network_rate":
        network_status = bindparam(
            "out_of_network_status",
            "out_of_network",
            type_=String(),
        )
        return (
            cast(
                func.sum(cast(providers.c.network_status == network_status, Integer())),
                Numeric(12, 6),
            )
            / func.nullif(func.count(claim_lines.c.id), 0)
        ).label(metric_id)
    if metric_id == "premium_per_member":
        return (
            func.sum(premium.c.earned_amount)
            / func.nullif(func.count(premium.c.member_id.distinct()), 0)
        ).label(metric_id)
    if metric_id == "case_reserves":
        return func.sum(reserves.c.case_reserve_amount).label(metric_id)
    raise ValueError(f"unsupported additional metric: {metric_id}")


def _aggregate_statement(plan: LogicalPlan, source, filters, metric_column, date_column):
    group_key = plan.group_by[0] if plan.group_by else None
    group_expression = _group_expression(group_key, date_column)
    if group_expression is None:
        return select(metric_column).select_from(source).where(*filters)

    return (
        select(group_expression.label(group_key), metric_column)
        .select_from(source)
        .where(*filters)
        .group_by(group_expression)
        .order_by(metric_column.element.desc())
        .limit(bindparam("result_limit", plan.result_shape.max_rows, type_=Integer()))
    )


def _group_expression(group_key: str | None, date_column=None):
    if group_key == "month" and date_column is not None:
        return func.date_trunc("month", date_column)
    if group_key == "plan_tier":
        return plans.c.plan_tier
    if group_key == "region":
        return members.c.region
    if group_key == "diagnosis_category":
        return claim_lines.c.diagnosis_category
    return None


def _compact_sql(plan: LogicalPlan) -> str:
    definitions = {
        "claim_count": ("semantic.claims", "incurred_date", "COUNT(DISTINCT claim_id)"),
        "covered_members": (
            "semantic.member_coverage",
            "coverage_month",
            "COUNT(DISTINCT member_id)",
        ),
        "open_claim_rate": (
            "semantic.claims",
            "incurred_date",
            "SUM(open_claim_count) / NULLIF(COUNT(*), 0)",
        ),
        "out_of_network_rate": (
            "semantic.claim_lines",
            "service_date",
            "SUM(out_of_network_count) / NULLIF(COUNT(*), 0)",
        ),
        "premium_per_member": (
            "semantic.premium",
            "coverage_month",
            "SUM(earned_amount) / NULLIF(COUNT(DISTINCT member_id), 0)",
        ),
        "case_reserves": (
            "semantic.case_reserves",
            "snapshot_date",
            "SUM(case_reserve_amount)",
        ),
    }
    source, date_column, expression = definitions[plan.metric.id]
    group_key = plan.group_by[0] if plan.group_by else None
    lines = ["SELECT"]
    if group_key:
        lines.extend([f"    {group_key},", f"    {expression} AS {plan.metric.id}"])
    else:
        lines.append(f"    {expression} AS {plan.metric.id}")
    lines.extend(
        [
            f"FROM {source}",
            f"WHERE {date_column} BETWEEN %(start_date)s AND %(end_date)s",
        ]
    )
    if plan.plan_tier:
        lines.append("  AND plan_tier = %(plan_tier)s")
    if group_key:
        lines.extend(
            [
                f"GROUP BY {group_key}",
                f"ORDER BY {plan.metric.id} DESC",
                "LIMIT %(result_limit)s",
            ]
        )
    return "\n".join(lines)
