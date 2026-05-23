def loss_ratio_sql(has_plan_tier: bool) -> str:
    """Return SQLite SQL for the loss-ratio demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    return f"""
        WITH claim_totals AS (
            SELECT
                claims.member_id AS member_id,
                SUM(claims.net_incurred_amount) AS incurred_claims
            FROM claims
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE claims.incurred_date BETWEEN :start_date AND :end_date
              AND claims.status != :excluded_status
              {plan_filter}
            GROUP BY claims.member_id
        ),
        premium_totals AS (
            SELECT
                premium.member_id AS member_id,
                SUM(premium.earned_amount) AS earned_premium
            FROM premium
            JOIN members ON premium.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            WHERE premium.coverage_month BETWEEN :start_date AND :end_date
              {plan_filter}
            GROUP BY premium.member_id
        )
        SELECT
            SUM(claim_totals.incurred_claims)
            / NULLIF(SUM(premium_totals.earned_premium), 0) AS loss_ratio
        FROM claim_totals
        JOIN premium_totals ON claim_totals.member_id = premium_totals.member_id
    """


def paid_claims_sql(has_plan_tier: bool) -> str:
    """Return SQLite SQL for the paid-claims demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    return f"""
        SELECT SUM(claim_lines.net_paid_amount) AS paid_claims
        FROM claim_lines
        JOIN claims ON claim_lines.claim_id = claims.id
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claim_lines.paid_date BETWEEN :start_date AND :end_date
          {plan_filter}
    """


def incurred_claims_sql(has_plan_tier: bool) -> str:
    """Return SQLite SQL for the incurred-claims demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    return f"""
        SELECT SUM(claims.net_incurred_amount) AS incurred_claims
        FROM claims
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claims.incurred_date BETWEEN :start_date AND :end_date
          AND claims.status != :excluded_status
          {plan_filter}
    """


def claim_frequency_sql(has_plan_tier: bool) -> str:
    """Return SQLite SQL for the claim-frequency demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
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


def claim_severity_sql(has_plan_tier: bool) -> str:
    """Return SQLite SQL for the claim-severity demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    return f"""
        SELECT
            SUM(claim_lines.net_paid_amount)
            / NULLIF(COUNT(DISTINCT claims.id), 0) AS claim_severity
        FROM claim_lines
        JOIN claims ON claim_lines.claim_id = claims.id
        JOIN members ON claims.member_id = members.id
        JOIN plans ON members.plan_id = plans.id
        WHERE claim_lines.paid_date BETWEEN :start_date AND :end_date
          AND claims.status = :closed_status
          {plan_filter}
    """


def decline_rate_sql(has_plan_tier: bool, group_by: tuple[str, ...] = ()) -> str:
    """Return SQLite SQL for the decline-rate demo query."""
    plan_filter = "AND plans.plan_tier = :plan_tier" if has_plan_tier else ""
    if group_by == ("consultant_specialty",):
        return f"""
            SELECT
                providers.specialty AS consultant_specialty,
                SUM(CASE WHEN claim_lines.declined_amount > 0 THEN 1 ELSE 0 END) * 1.0
                / NULLIF(COUNT(claim_lines.id), 0) AS decline_rate
            FROM claim_lines
            JOIN claims ON claim_lines.claim_id = claims.id
            JOIN members ON claims.member_id = members.id
            JOIN plans ON members.plan_id = plans.id
            JOIN providers ON claim_lines.provider_id = providers.id
            WHERE claim_lines.service_date BETWEEN :start_date AND :end_date
              {plan_filter}
            GROUP BY providers.specialty
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
