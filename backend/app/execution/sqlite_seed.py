import sqlite3
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.seeds.synthetic import SeedData


def prepare_demo_database(connection: sqlite3.Connection, seed_data: SeedData) -> None:
    """Create minimal SQLite tables and insert deterministic demo rows."""
    _create_demo_tables(connection)
    _insert_demo_rows(connection, seed_data)


def to_sqlite_parameters(parameters: dict[str, object]) -> dict[str, object]:
    """Convert generated query parameters into SQLite-friendly values."""
    return {key: _sqlite_value(value) for key, value in parameters.items()}


def _create_demo_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE plans (
            id TEXT PRIMARY KEY,
            plan_code TEXT NOT NULL,
            plan_tier TEXT NOT NULL
        );

        CREATE TABLE members (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            region TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            enrolled_from TEXT NOT NULL,
            enrolled_to TEXT
        );

        CREATE TABLE providers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            network_status TEXT NOT NULL,
            region TEXT NOT NULL
        );

        CREATE TABLE claims (
            id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            incurred_date TEXT NOT NULL,
            status TEXT NOT NULL,
            net_incurred_amount REAL NOT NULL
        );

        CREATE TABLE claim_lines (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            service_date TEXT NOT NULL,
            paid_date TEXT,
            net_paid_amount REAL NOT NULL,
            declined_amount REAL NOT NULL
        );

        CREATE TABLE enrolment_months (
            id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            coverage_month TEXT NOT NULL,
            member_months REAL NOT NULL
        );

        CREATE TABLE premium (
            id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            coverage_month TEXT NOT NULL,
            earned_amount REAL NOT NULL
        );

        CREATE TABLE reserves (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            case_reserve_amount REAL NOT NULL
        );
        """
    )


def _insert_demo_rows(connection: sqlite3.Connection, seed_data: SeedData) -> None:
    connection.executemany(
        """
        INSERT INTO plans (id, plan_code, plan_tier)
        VALUES (:id, :plan_code, :plan_tier)
        """,
        [_clean_row(row, ("id", "plan_code", "plan_tier")) for row in seed_data.plans],
    )
    connection.executemany(
        """
        INSERT INTO providers (id, name, specialty, network_status, region)
        VALUES (:id, :name, :specialty, :network_status, :region)
        """,
        [
            _clean_row(
                row,
                ("id", "name", "specialty", "network_status", "region"),
            )
            for row in seed_data.providers
        ],
    )
    connection.executemany(
        """
        INSERT INTO members (
            id, plan_id, region, date_of_birth, enrolled_from, enrolled_to
        )
        VALUES (:id, :plan_id, :region, :date_of_birth, :enrolled_from, :enrolled_to)
        """,
        [
            _clean_row(
                row,
                (
                    "id",
                    "plan_id",
                    "region",
                    "date_of_birth",
                    "enrolled_from",
                    "enrolled_to",
                ),
            )
            for row in seed_data.members
        ],
    )
    connection.executemany(
        """
        INSERT INTO claims (id, member_id, incurred_date, status, net_incurred_amount)
        VALUES (:id, :member_id, :incurred_date, :status, :net_incurred_amount)
        """,
        [
            _clean_row(
                row,
                ("id", "member_id", "incurred_date", "status", "net_incurred_amount"),
            )
            for row in seed_data.claims
        ],
    )
    connection.executemany(
        """
        INSERT INTO reserves (id, claim_id, snapshot_date, case_reserve_amount)
        VALUES (:id, :claim_id, :snapshot_date, :case_reserve_amount)
        """,
        [
            _clean_row(
                row,
                ("id", "claim_id", "snapshot_date", "case_reserve_amount"),
            )
            for row in seed_data.reserves
        ],
    )
    connection.executemany(
        """
        INSERT INTO claim_lines (
            id, claim_id, provider_id, service_date, paid_date, net_paid_amount,
            declined_amount
        )
        VALUES (
            :id, :claim_id, :provider_id, :service_date, :paid_date,
            :net_paid_amount, :declined_amount
        )
        """,
        [
            _clean_row(
                row,
                (
                    "id",
                    "claim_id",
                    "provider_id",
                    "service_date",
                    "paid_date",
                    "net_paid_amount",
                    "declined_amount",
                ),
            )
            for row in seed_data.claim_lines
        ],
    )
    connection.executemany(
        """
        INSERT INTO enrolment_months (id, member_id, coverage_month, member_months)
        VALUES (:id, :member_id, :coverage_month, :member_months)
        """,
        [
            _clean_row(row, ("id", "member_id", "coverage_month", "member_months"))
            for row in seed_data.enrolment_months
        ],
    )
    connection.executemany(
        """
        INSERT INTO premium (id, member_id, coverage_month, earned_amount)
        VALUES (:id, :member_id, :coverage_month, :earned_amount)
        """,
        [
            _clean_row(row, ("id", "member_id", "coverage_month", "earned_amount"))
            for row in seed_data.premium
        ],
    )


def _clean_row(row: dict[str, object], fields: tuple[str, ...]) -> dict[str, object]:
    return {field: _sqlite_value(row[field]) for field in fields}


def _sqlite_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value
