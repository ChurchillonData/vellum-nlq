"""Run the local Postgres proof workflow for Vellum-NLQ."""

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.db.proof import run_postgres_proof


def parse_args() -> argparse.Namespace:
    """Parse proof workflow options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        choices=("none", "local", "portfolio"),
        default="none",
        help=(
            "Seed profile to load before the smoke test. "
            "'none' checks an already seeded database."
        ),
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run the optional live Postgres integration test after smoke checks.",
    )
    parser.add_argument(
        "--skip-start",
        action="store_true",
        help="Skip docker compose startup when Postgres is already running elsewhere.",
    )
    return parser.parse_args()


def main() -> int:
    """Run local Postgres proof steps in order."""
    args = parse_args()
    return run_postgres_proof(
        seed=args.seed,
        integration=args.integration,
        skip_start=args.skip_start,
    )


if __name__ == "__main__":
    raise SystemExit(main())
