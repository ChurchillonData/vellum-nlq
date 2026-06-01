"""Reset the local Docker Postgres database for Vellum-NLQ development."""

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def parse_args() -> argparse.Namespace:
    """Parse reset workflow options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually run the destructive local reset. Without this, commands are only printed.",
    )
    return parser.parse_args()


def main() -> None:
    """Run or preview the local Postgres reset workflow."""
    args = parse_args()
    commands = [
        (["docker", "compose", "down", "-v"], ROOT),
        (["docker", "compose", "up", "-d", "postgres"], ROOT),
        ([sys.executable, "-m", "alembic", "upgrade", "head"], BACKEND),
        ([sys.executable, "-m", "app.dbcheck"], BACKEND),
    ]

    if not args.yes:
        print("Dry run. Add --yes to delete and recreate the local Docker database volume.")
        for command, cwd in commands:
            print(f"{cwd}> {' '.join(command)}")
        return

    print("Resetting local Docker Postgres volume. This deletes local database data only.")
    for index, (command, cwd) in enumerate(commands):
        if index == 2:
            print("Waiting for Postgres to accept connections...")
            time.sleep(3)
        print(f"{cwd}> {' '.join(command)}")
        subprocess.run(command, cwd=cwd, check=True)

    print("Local Postgres reset complete.")


if __name__ == "__main__":
    main()
