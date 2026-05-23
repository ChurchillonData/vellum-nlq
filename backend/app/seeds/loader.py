from sqlalchemy import create_engine

from app.config import get_settings
from app.db import schema
from app.seeds.synthetic import SeedData


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
    engine = create_engine(get_settings().seed_database_url)

    with engine.begin() as connection:
        for table, _ in reversed(LOAD_ORDER):
            connection.execute(table.delete())

        for table, attribute_name in LOAD_ORDER:
            rows = getattr(seed_data, attribute_name)
            if rows:
                connection.execute(table.insert(), rows)
