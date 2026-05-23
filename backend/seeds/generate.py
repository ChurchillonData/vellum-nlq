"""Load deterministic synthetic claims data into the development database."""

import argparse

from app.seeds.loader import load_seed_data
from app.seeds.synthetic import build_seed_data


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
