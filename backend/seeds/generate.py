"""Load deterministic synthetic claims data into the development database."""

import argparse
from dataclasses import dataclass

from app.seeds.loader import load_seed_data
from app.seeds.synthetic import build_seed_data


@dataclass(frozen=True)
class SeedProfile:
    """A named data volume for local and portfolio demos."""

    member_count: int
    month_count: int
    chunk_size: int


SEED_PROFILES = {
    "local": SeedProfile(member_count=2_000, month_count=18, chunk_size=2_000),
    "portfolio": SeedProfile(member_count=200_000, month_count=18, chunk_size=10_000),
}


def parse_args() -> argparse.Namespace:
    """Parse CLI options for local data generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=sorted(SEED_PROFILES),
        default="local",
        help="Named data volume to generate.",
    )
    parser.add_argument("--member-count", type=int)
    parser.add_argument("--month-count", type=int)
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Members to generate and insert per batch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate chunks and print row counts without loading Postgres.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate and load synthetic development data."""
    args = parse_args()
    profile = SEED_PROFILES[args.profile]
    member_count = args.member_count or profile.member_count
    month_count = args.month_count or profile.month_count
    chunk_size = args.chunk_size or profile.chunk_size

    if member_count < 1:
        raise ValueError("member_count must be at least 1")
    if month_count < 1:
        raise ValueError("month_count must be at least 1")
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    totals = {
        "members": 0,
        "claims": 0,
        "premium": 0,
    }

    for start_index in range(0, member_count, chunk_size):
        current_chunk_size = min(chunk_size, member_count - start_index)
        seed_data = build_seed_data(
            current_chunk_size,
            month_count=month_count,
            start_member_index=start_index,
            include_reference_data=start_index == 0,
        )
        if not args.dry_run:
            load_seed_data(seed_data, replace=start_index == 0)
        totals["members"] += len(seed_data.members)
        totals["claims"] += len(seed_data.claims)
        totals["premium"] += len(seed_data.premium)
        print(
            f"{'Prepared' if args.dry_run else 'Loaded'} chunk "
            f"{start_index + current_chunk_size:,}/{member_count:,} members..."
        )

    print(
        f"{'Prepared' if args.dry_run else 'Seeded'} "
        f"{totals['members']:,} members, "
        f"{totals['claims']:,} claims, "
        f"{totals['premium']:,} premium rows."
    )


if __name__ == "__main__":
    main()
