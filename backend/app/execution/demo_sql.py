def loss_ratio_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the loss-ratio demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    claim_group_select, claim_group_column, group_key = _member_group_parts(
        group_by,
        "claims.incurred_date",
    )
    premium_group_select, premium_group_column, _ = _member_group_parts(
        group_by,
        "premium.coverage_month",
    )
    if group_key:
        return f"""
            WITH claim_totals AS (
                SELECT
                    {claim_group_select},
                    SUM(claims.net_incurred_amount) AS incurred_claims
                FROM claims
                JOIN members ON claims.member_id = members.id
                JOIN plans ON members.plan_id = plans.id
                WHERE claims.incurred_date BETWEEN :start_date AND :end_date
                  AND claims.status != :excluded_status
                  {plan_filter}
                GROUP BY {claim_group_column}
            ),
            premium_totals AS (
                SELECT
                    {premium_group_select},
                    SUM(premium.earned_amount) AS earned_premium
                FROM premium
                JOIN members ON premium.member_id = members.id
                JOIN plans ON members.plan_id = plans.id
                WHERE premium.coverage_month BETWEEN :start_date AND :end_date
                  {plan_filter}
                GROUP BY {premium_group_column}
            )
            SELECT
                claim_totals.{group_key} AS {group_key},
                SUM(claim_totals.incurred_claims)
                / NULLIF(SUM(premium_totals.earned_premium), 0) AS loss_ratio
            FROM claim_totals
            JOIN premium_totals ON claim_totals.{group_key} = premium_totals.{group_key}
            GROUP BY claim_totals.{group_key}
            ORDER BY loss_ratio DESC
            LIMIT :result_limit
        """

    return f"""
        WITH claim_totals AS (
            SELECT
                SUM(claims.net_incurred_amount) AS incurred_claims
            FROM claims
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE claims.incurred_date BETWEEN :start_date AND :end_date
              AND claims.status != :excluded_status
              {plan_filter}
        ),
        premium_totals AS (
            SELECT
                SUM(premium.earned_amount) AS earned_premium
            FROM premium
            JOIN members ON premium.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE premium.coverage_month BETWEEN :start_date AND :end_date
              {plan_filter}
        )
        SELECT
            SUM(claim_totals.incurred_claims)
            / NULLIF(SUM(premium_totals.earned_premium), 0) AS loss_ratio
        FROM claim_totals
        JOIN premium_totals ON 1 = 1
    """


def paid_claims_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the paid-claims demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    group_select, group_column, group_key = _member_group_parts(
        group_by,
        "claim_lines.paid_date",
    )
    select_prefix = f"{group_select}, " if group_key else ""
    group_tail = _group_tail(group_column, "paid_claims")
    return f"""
        SELECT {select_prefix}SUM(claim_lines.net_paid_amount) AS paid_claims
        FROM claim_lines
        JOIN claims ON claim_lines.claim_id = claims.id
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claim_lines.paid_date BETWEEN :start_date AND :end_date
          {plan_filter}
        {group_tail}
    """


def incurred_claims_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the incurred-claims demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    group_select, group_column, group_key = _member_group_parts(
        group_by,
        "claims.incurred_date",
    )
    select_prefix = f"{group_select}, " if group_key else ""
    group_tail = _group_tail(group_column, "incurred_claims")
    return f"""
        SELECT {select_prefix}SUM(claims.net_incurred_amount) AS incurred_claims
        FROM claims
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claims.incurred_date BETWEEN :start_date AND :end_date
          AND claims.status != :excluded_status
          {plan_filter}
        {group_tail}
    """


def claim_frequency_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the claim-frequency demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    claim_group_select, claim_group_column, group_key = _member_group_parts(
        group_by,
        "claims.incurred_date",
    )
    member_month_group_select, member_month_group_column, _ = _member_group_parts(
        group_by,
        "enrolment_months.coverage_month",
    )
    if group_key:
        return f"""
            WITH claim_counts AS (
                SELECT
                    {claim_group_select},
                    COUNT(DISTINCT claims.id) AS claim_count
                FROM claims
                JOIN members ON claims.member_id = members.id
                JOIN plans ON members.plan_id = plans.id
                WHERE claims.incurred_date BETWEEN :start_date AND :end_date
                  AND claims.status != :excluded_status
                  {plan_filter}
                GROUP BY {claim_group_column}
            ),
            member_months AS (
                SELECT
                    {member_month_group_select},
                    SUM(enrolment_months.member_months) AS member_months
                FROM enrolment_months
                JOIN members ON enrolment_months.member_id = members.id
                JOIN plans ON members.plan_id = plans.id
                WHERE enrolment_months.coverage_month BETWEEN :start_date AND :end_date
                  {plan_filter}
                GROUP BY {member_month_group_column}
            )
            SELECT
                claim_counts.{group_key} AS {group_key},
                claim_counts.claim_count * 1000
                / NULLIF(member_months.member_months, 0) AS claim_frequency
            FROM claim_counts
            JOIN member_months ON claim_counts.{group_key} = member_months.{group_key}
            ORDER BY claim_frequency DESC
            LIMIT :result_limit
        """

    return f"""
        WITH claim_counts AS (
            SELECT COUNT(DISTINCT claims.id) AS claim_count
            FROM claims
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE claims.incurred_date BETWEEN :start_date AND :end_date
              AND claims.status != :excluded_status
              {plan_filter}
        ),
        member_months AS (
            SELECT SUM(enrolment_months.member_months) AS member_months
            FROM enrolment_months
            JOIN members ON enrolment_months.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE enrolment_months.coverage_month BETWEEN :start_date AND :end_date
              {plan_filter}
        )
        SELECT claim_counts.claim_count * 1000
               / NULLIF(member_months.member_months, 0) AS claim_frequency
        FROM claim_counts
        JOIN member_months ON 1 = 1
    """


def claim_severity_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the claim-severity demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    group_select, group_column, group_key = _member_group_parts(
        group_by,
        "claim_lines.paid_date",
    )
    select_prefix = f"{group_select}, " if group_key else ""
    group_tail = _group_tail(group_column, "claim_severity")
    return f"""
        SELECT
            {select_prefix}
            SUM(claim_lines.net_paid_amount)
            / NULLIF(COUNT(DISTINCT claims.id), 0) AS claim_severity
        FROM claim_lines
        JOIN claims ON claim_lines.claim_id = claims.id
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claim_lines.paid_date BETWEEN :start_date AND :end_date
          AND claims.status = :closed_status
          {plan_filter}
        {group_tail}
    """


def decline_rate_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the decline-rate demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    group_select, group_column, group_key = _member_group_parts(
        group_by,
        "claim_lines.service_date",
    )
    if group_by == ("consultant_specialty",):
        group_select = "providers.specialty AS consultant_specialty"
        group_column = "providers.specialty"
        return f"""
            SELECT
                {group_select},
                SUM(CASE WHEN claim_lines.declined_amount > 0 THEN 1 ELSE 0 END) * 1.0
                / NULLIF(COUNT(claim_lines.id), 0) AS decline_rate
            FROM claim_lines
            JOIN claims ON claim_lines.claim_id = claims.id
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            JOIN providers ON claim_lines.provider_id = providers.id
            WHERE claim_lines.service_date BETWEEN :start_date AND :end_date
              {plan_filter}
            GROUP BY {group_column}
            ORDER BY decline_rate DESC
            LIMIT :result_limit
        """

    if group_key:
        return f"""
            SELECT
                {group_select},
                SUM(CASE WHEN claim_lines.declined_amount > 0 THEN 1 ELSE 0 END) * 1.0
                / NULLIF(COUNT(claim_lines.id), 0) AS decline_rate
            FROM claim_lines
            JOIN claims ON claim_lines.claim_id = claims.id
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE claim_lines.service_date BETWEEN :start_date AND :end_date
              {plan_filter}
            GROUP BY {group_column}
            ORDER BY decline_rate DESC
            LIMIT :result_limit
        """

    return f"""
        SELECT
            SUM(CASE WHEN claim_lines.declined_amount > 0 THEN 1 ELSE 0 END) * 1.0
            / NULLIF(COUNT(claim_lines.id), 0) AS decline_rate
        FROM claim_lines
        JOIN claims ON claim_lines.claim_id = claims.id
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claim_lines.service_date BETWEEN :start_date AND :end_date
          {plan_filter}
    """


def additional_metric_sql(
    metric_id: str,
    has_plan_tier: bool,
    group_by: tuple[str, ...] = (),
) -> str:
    """Return SQLite SQL for one additional governed aggregate metric."""
    definitions = {
        "claim_count": (
            "COUNT(DISTINCT claims.id)",
            "claims JOIN members ON claims.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id",
            "claims.incurred_date",
            "AND claims.status != :excluded_status",
        ),
        "covered_members": (
            "COUNT(DISTINCT enrolment_months.member_id)",
            "enrolment_months "
            "JOIN members ON enrolment_months.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id",
            "enrolment_months.coverage_month",
            "",
        ),
        "open_claim_rate": (
            "SUM(CASE WHEN claims.status = :open_status THEN 1 ELSE 0 END) * 1.0 "
            "/ NULLIF(COUNT(claims.id), 0)",
            "claims JOIN members ON claims.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id",
            "claims.incurred_date",
            "",
        ),
        "out_of_network_rate": (
            "SUM(CASE WHEN providers.network_status = :out_of_network_status "
            "THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(claim_lines.id), 0)",
            "claim_lines JOIN claims ON claim_lines.claim_id = claims.id "
            "JOIN members ON claims.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id "
            "JOIN providers ON claim_lines.provider_id = providers.id",
            "claim_lines.service_date",
            "",
        ),
        "premium_per_member": (
            "SUM(premium.earned_amount) * 1.0 "
            "/ NULLIF(COUNT(DISTINCT premium.member_id), 0)",
            "premium JOIN members ON premium.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id",
            "premium.coverage_month",
            "",
        ),
        "case_reserves": (
            "SUM(reserves.case_reserve_amount)",
            "reserves JOIN claims ON reserves.claim_id = claims.id "
            "JOIN members ON claims.member_id = members.id "
            "JOIN plans ON members.plan_id = plans.id",
            "reserves.snapshot_date",
            "",
        ),
    }
    expression, source, date_column, extra_filter = definitions[metric_id]
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    group_select, group_column, group_key = _member_group_parts(group_by, date_column)
    select_prefix = f"{group_select}, " if group_key else ""
    group_tail = _group_tail(group_column, metric_id)
    return f"""
        SELECT {select_prefix}{expression} AS {metric_id}
        FROM {source}
        WHERE {date_column} BETWEEN :start_date AND :end_date
          {extra_filter}
          {plan_filter}
        {group_tail}
    """


def _member_group_parts(
    group_by: tuple[str, ...],
    date_column: str | None = None,
) -> tuple[str, str, str]:
    if group_by == ("month",) and date_column:
        return (
            f"substr({date_column}, 1, 7) AS month",
            f"substr({date_column}, 1, 7)",
            "month",
        )
    if group_by == ("plan_tier",):
        return "plans.plan_tier AS plan_tier", "plans.plan_tier", "plan_tier"
    if group_by == ("region",):
        return "members.region AS region", "members.region", "region"
    if group_by == ("diagnosis_category",):
        return (
            "claim_lines.diagnosis_category AS diagnosis_category",
            "claim_lines.diagnosis_category",
            "diagnosis_category",
        )
    return "", "", ""


def _group_tail(group_column: str, metric_alias: str) -> str:
    if not group_column:
        return ""
    return f"""
        GROUP BY {group_column}
        ORDER BY {metric_alias} DESC
        LIMIT :result_limit
    """
