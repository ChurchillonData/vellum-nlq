import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"


ProofCommand = tuple[str, list[str], Path, dict[str, str] | None]


def run_postgres_proof(
    seed: str,
    integration: bool,
    skip_start: bool,
) -> int:
    """Run selected local Postgres proof commands in order."""
    print("Vellum-NLQ Postgres proof")

    for label, command, cwd, env in proof_commands(seed, integration, skip_start):
        print(f"\n[{label}] {cwd}> {' '.join(command)}")
        completed = subprocess.run(command, cwd=cwd, env=env, check=False)
        if completed.returncode != 0:
            print(f"\nPostgres proof failed at step: {label}")
            return completed.returncode

    print("\nPostgres proof completed successfully.")
    return 0


def proof_commands(
    seed: str,
    integration: bool,
    skip_start: bool,
) -> list[ProofCommand]:
    """Build the ordered commands for the selected proof workflow."""
    commands: list[ProofCommand] = []

    if not skip_start:
        commands.append(
            ("start postgres", ["docker", "compose", "up", "-d", "postgres"], ROOT, None)
        )

    commands.extend(
        [
            ("run migrations", [sys.executable, "-m", "alembic", "upgrade", "head"], BACKEND, None),
            ("check roles", [sys.executable, "-m", "app.dbcheck"], BACKEND, None),
        ]
    )

    if seed != "none":
        commands.append(
            (
                f"seed {seed}",
                [sys.executable, "seeds/generate.py", "--profile", seed],
                BACKEND,
                None,
            )
        )

    commands.append(("smoke test", [sys.executable, "-m", "app.postgres_smoke"], BACKEND, None))

    if integration:
        env = os.environ.copy()
        env["VELLUM_RUN_POSTGRES_INTEGRATION"] = "1"
        commands.append(
            (
                "integration test",
                [sys.executable, "-m", "pytest", "tests/integration", "-q"],
                BACKEND,
                env,
            )
        )

    return commands
