from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5


Row = dict[str, object]


@dataclass
class SeedData:
    """Synthetic rows grouped by database table."""

    plans: list[Row] = field(default_factory=list)
    members: list[Row] = field(default_factory=list)
    providers: list[Row] = field(default_factory=list)
    enrolment_months: list[Row] = field(default_factory=list)
    claims: list[Row] = field(default_factory=list)
    claim_lines: list[Row] = field(default_factory=list)
    claim_status_history: list[Row] = field(default_factory=list)
    reserves: list[Row] = field(default_factory=list)
    premium: list[Row] = field(default_factory=list)
    declines: list[Row] = field(default_factory=list)


def build_seed_data(
    member_count: int,
    month_count: int = 18,
    start_month: date = date(2025, 1, 1),
    start_member_index: int = 0,
    include_reference_data: bool = True,
) -> SeedData:
    """Build deterministic UK PMI-shaped data for local development."""
    if member_count < 1:
        raise ValueError("member_count must be at least 1")
    if month_count < 1:
        raise ValueError("month_count must be at least 1")
    if start_member_index < 0:
        raise ValueError("start_member_index must be at least 0")

    reference_plans = _plan_rows()
    reference_providers = _provider_rows()
    data = SeedData(
        plans=reference_plans if include_reference_data else [],
        providers=reference_providers if include_reference_data else [],
    )
    coverage_months = _coverage_months(start_month, month_count)

    for member_index in range(start_member_index, start_member_index + member_count):
        member_id = _row_id("member", member_index)
        plan = reference_plans[member_index % len(reference_plans)]
        data.members.append(_member_row(member_id, plan["id"], member_index, start_month))

        for coverage_month in coverage_months:
            data.enrolment_months.append(
                {
                    "id": _row_id("enrolment-month", member_index, coverage_month.isoformat()),
                    "member_id": member_id,
                    "coverage_month": coverage_month,
                    "member_months": Decimal("1.00"),
                }
            )
            data.premium.append(
                {
                    "id": _row_id("premium", member_index, coverage_month.isoformat()),
                    "member_id": member_id,
                    "coverage_month": coverage_month,
                    "earned_amount": _premium_amount(plan["plan_tier"]),
                }
            )

        if member_index % 4 == 0:
            incurred_month = coverage_months[(member_index + 8) % len(coverage_months)]
            _append_claim_rows(
                data,
                reference_providers,
                member_id,
                member_index,
                incurred_month,
                claim_number=1,
            )

        if member_index % 15 == 0:
            incurred_month = coverage_months[(member_index + 3) % len(coverage_months)]
            _append_claim_rows(
                data,
                reference_providers,
                member_id,
                member_index,
                incurred_month,
                claim_number=2,
            )

    return data


def _plan_rows() -> list[Row]:
    return [
        {
            "id": _row_id("plan", "essential"),
            "plan_code": "ESSENTIAL",
            "plan_tier": "Essential",
            "hospital_network": "Core",
            "excess_amount": Decimal("250.00"),
        },
        {
            "id": _row_id("plan", "comprehensive"),
            "plan_code": "COMPREHENSIVE",
            "plan_tier": "Comprehensive",
            "hospital_network": "Extended",
            "excess_amount": Decimal("100.00"),
        },
        {
            "id": _row_id("plan", "executive"),
            "plan_code": "EXECUTIVE",
            "plan_tier": "Executive",
            "hospital_network": "National",
            "excess_amount": Decimal("0.00"),
        },
    ]


def _provider_rows() -> list[Row]:
    specialties = [
        ("Harbour Cardiology", "Cardiology", "in_network", "London"),
        ("Northgate Orthopaedics", "Orthopaedics", "in_network", "North West"),
        ("Cedar Diagnostics", "Radiology", "in_network", "Midlands"),
        ("Westbridge Clinic", "General Medicine", "out_of_network", "South East"),
    ]
    return [
        {
            "id": _row_id("provider", index),
            "name": name,
            "specialty": specialty,
            "network_status": network_status,
            "region": region,
        }
        for index, (name, specialty, network_status, region) in enumerate(specialties)
    ]


def _member_row(member_id: UUID, plan_id: object, member_index: int, start_month: date) -> Row:
    regions = ["London", "South East", "Midlands", "North West", "Scotland"]
    birth_year = 1955 + (member_index % 45)
    return {
        "id": member_id,
        "plan_id": plan_id,
        "region": regions[member_index % len(regions)],
        "date_of_birth": date(birth_year, (member_index % 12) + 1, (member_index % 27) + 1),
        "enrolled_from": start_month,
        "enrolled_to": None,
    }


def _append_claim_rows(
    data: SeedData,
    providers: list[Row],
    member_id: UUID,
    member_index: int,
    incurred_month: date,
    claim_number: int,
) -> None:
    claim_id = _row_id("claim", member_index, claim_number)
    line_id = _row_id("claim-line", member_index, claim_number)
    provider = providers[(member_index + claim_number) % len(providers)]
    incurred_date = incurred_month + timedelta(days=(member_index % 20) + 1)
    received_date = incurred_date + timedelta(days=2)
    adjudicated_date = received_date + timedelta(days=5)
    status = _claim_status(member_index, claim_number)
    paid_amount = _paid_amount(member_index, status)
    reserve_amount = Decimal("180.00") if status == "open" else Decimal("0.00")
    declined_amount = Decimal("320.00") if status == "declined" else Decimal("0.00")
    closed_date = adjudicated_date if status in {"closed", "declined"} else None

    data.claims.append(
        {
            "id": claim_id,
            "member_id": member_id,
            "incurred_date": incurred_date,
            "received_date": received_date,
            "adjudicated_date": adjudicated_date,
            "closed_date": closed_date,
            "status": status,
            "net_incurred_amount": paid_amount + reserve_amount,
        }
    )
    data.claim_lines.append(
        {
            "id": line_id,
            "claim_id": claim_id,
            "provider_id": provider["id"],
            "service_date": incurred_date,
            "procedure_code": f"PROC-{(member_index % 6) + 1:02d}",
            "diagnosis_category": _diagnosis_category(member_index),
            "paid_date": adjudicated_date if paid_amount else None,
            "net_paid_amount": paid_amount,
            "declined_amount": declined_amount,
        }
    )
    data.reserves.append(
        {
            "id": _row_id("reserve", member_index, claim_number),
            "claim_id": claim_id,
            "snapshot_date": adjudicated_date,
            "case_reserve_amount": reserve_amount,
        }
    )
    data.claim_status_history.extend(
        [
            _status_row(claim_id, "received", received_date, claim_number, 1),
            _status_row(claim_id, status, adjudicated_date, claim_number, 2),
        ]
    )

    if status == "declined":
        data.declines.append(
            {
                "id": _row_id("decline", member_index, claim_number),
                "claim_line_id": line_id,
                "reason_code": "POLICY_EXCLUSION",
                "reason_text": "Service falls outside this plan's covered benefits.",
            }
        )


def _status_row(
    claim_id: UUID,
    status: str,
    changed_on: date,
    claim_number: int,
    sequence: int,
) -> Row:
    return {
        "id": _row_id("status", claim_id, claim_number, sequence),
        "claim_id": claim_id,
        "status": status,
        "changed_at": datetime.combine(changed_on, time(hour=9 + sequence), UTC),
    }


def _claim_status(member_index: int, claim_number: int) -> str:
    if (member_index + claim_number) % 13 == 0:
        return "declined"
    if (member_index + claim_number) % 9 == 0:
        return "open"
    return "closed"


def _paid_amount(member_index: int, status: str) -> Decimal:
    if status == "declined":
        return Decimal("0.00")
    return Decimal("450.00") + Decimal((member_index % 8) * 85)


def _premium_amount(plan_tier: object) -> Decimal:
    amounts = {
        "Essential": Decimal("210.00"),
        "Comprehensive": Decimal("330.00"),
        "Executive": Decimal("470.00"),
    }
    return amounts[str(plan_tier)]


def _diagnosis_category(member_index: int) -> str:
    categories = ["Musculoskeletal", "Cardiac", "Diagnostics", "General"]
    return categories[member_index % len(categories)]


def _coverage_months(start_month: date, month_count: int) -> list[date]:
    return [_add_months(start_month, offset) for offset in range(month_count)]


def _add_months(value: date, offset: int) -> date:
    month_index = value.month - 1 + offset
    return date(value.year + month_index // 12, (month_index % 12) + 1, 1)


def _row_id(*parts: object) -> UUID:
    stable_key = ":".join(str(part) for part in parts)
    return uuid5(NAMESPACE_URL, f"vellum:{stable_key}")
