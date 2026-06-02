"""Load deterministic synthetic claims data into the development database."""

import argparse
from dataclasses import dataclass

from app.seeds.loader import load_seed_data
from app.seeds.loader import LOAD_ORDER
from app.seeds.synthetic import SeedData, build_seed_data


@dataclass(frozen=True)
class SeedProfile:
    """A named data volume for local and portfolio demos."""

    member_count: int
    month_count: int
    chunk_size: int


@dataclass(frozen=True)
class SeedRunConfig:
    """Resolved seed settings for one CLI run."""

    profile: str
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
    config = resolve_seed_config(
        profile_name=args.profile,
        member_count=args.member_count,
        month_count=args.month_count,
        chunk_size=args.chunk_size,
    )
    totals = empty_row_counts()
    chunks = chunk_ranges(config.member_count, config.chunk_size)

    print_seed_plan(config, chunk_count=len(chunks), dry_run=args.dry_run)

    for start_index, current_chunk_size in chunks:
        seed_data = build_seed_data(
            current_chunk_size,
            month_count=config.month_count,
            start_member_index=start_index,
            include_reference_data=start_index == 0,
        )
        if not args.dry_run:
            load_seed_data(seed_data, replace=start_index == 0)
        add_row_counts(totals, count_seed_rows(seed_data))
        print(
            f"{'Prepared' if args.dry_run else 'Loaded'} chunk "
            f"{start_index + current_chunk_size:,}/{config.member_count:,} members..."
        )

    print_seed_summary(totals, dry_run=args.dry_run)


def resolve_seed_config(
    profile_name: str,
    member_count: int | None = None,
    month_count: int | None = None,
    chunk_size: int | None = None,
) -> SeedRunConfig:
    """Resolve and validate seed settings from CLI options."""
    profile = SEED_PROFILES[profile_name]
    config = SeedRunConfig(
        profile=profile_name,
        member_count=profile.member_count if member_count is None else member_count,
        month_count=profile.month_count if month_count is None else month_count,
        chunk_size=profile.chunk_size if chunk_size is None else chunk_size,
    )

    if config.member_count < 1:
        raise ValueError("member_count must be at least 1")
    if config.month_count < 1:
        raise ValueError("month_count must be at least 1")
    if config.chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    return config


def chunk_ranges(member_count: int, chunk_size: int) -> list[tuple[int, int]]:
    """Return `(start_index, size)` pairs for chunked seed generation."""
    return [
        (start_index, min(chunk_size, member_count - start_index))
        for start_index in range(0, member_count, chunk_size)
    ]


def empty_row_counts() -> dict[str, int]:
    """Return zero counts for every loadable seed table."""
    return {attribute_name: 0 for _, attribute_name in LOAD_ORDER}


def count_seed_rows(seed_data: SeedData) -> dict[str, int]:
    """Count generated rows for every seed table."""
    return {
        attribute_name: len(getattr(seed_data, attribute_name))
        for _, attribute_name in LOAD_ORDER
    }


def add_row_counts(totals: dict[str, int], next_counts: dict[str, int]) -> None:
    """Add one chunk's table counts into the running totals."""
    for table_name, row_count in next_counts.items():
        totals[table_name] += row_count


def print_seed_plan(config: SeedRunConfig, chunk_count: int, dry_run: bool) -> None:
    """Print the seed run configuration before generation starts."""
    mode = "Dry run" if dry_run else "Load"
    print(
        f"{mode}: profile={config.profile}, "
        f"members={config.member_count:,}, "
        f"months={config.month_count:,}, "
        f"chunk_size={config.chunk_size:,}, "
        f"chunks={chunk_count:,}."
    )
    if dry_run:
        print("Dry run only: Postgres load skipped.")


def print_seed_summary(totals: dict[str, int], dry_run: bool) -> None:
    """Print table-level row counts after generation finishes."""
    print(f"{'Prepared' if dry_run else 'Seeded'} row counts:")
    for table_name, row_count in totals.items():
        print(f"  {table_name}: {row_count:,}")


if __name__ == "__main__":
    main()
