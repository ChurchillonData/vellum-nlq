"""Load deterministic synthetic claims data into the development database."""

import argparse

from sqlalchemy import create_engine

from app.config import get_settings
from app.db import schema
from app.seeds.synthetic import SeedData, build_seed_data


LOAD_ORDER = [
    (schema.plans, "plans"),
    (schema.members, "members"),
    (schema.providers, "providers"),
    (schema.enrolment_months, "enrolment_months"),
    (schema.claims, "claims"),
    (schema.claim_lines, "claim_lines"),
    (schema.claim_status_history, "claim_status_history"),
    (schema.reserves, "reserves"),
    (schema.premium, "premium"),
    (schema.declines, "declines"),
]


def load_seed_data(seed_data: SeedData) -> None:
    """Replace development rows with a fresh synthetic dataset."""
    engine = create_engine(get_settings().database_url)

    with engine.begin() as connection:
        for table, _ in reversed(LOAD_ORDER):
            connection.execute(table.delete())

        for table, attribute_name in LOAD_ORDER:
            rows = getattr(seed_data, attribute_name)
            if rows:
                connection.execute(table.insert(), rows)


def parse_args() -> argparse.Namespace:
    """Parse CLI options for local data generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member-count", type=int, default=2_000)
    parser.add_argument("--month-count", type=int, default=18)
    return parser.parse_args()


def main() -> None:
    """Generate and load synthetic development data."""
    args = parse_args()
    seed_data = build_seed_data(args.member_count, args.month_count)
    load_seed_data(seed_data)
    print(
        "Seeded "
        f"{len(seed_data.members)} members, "
        f"{len(seed_data.claims)} claims, "
        f"{len(seed_data.premium)} premium rows."
    )


if __name__ == "__main__":
    main()

