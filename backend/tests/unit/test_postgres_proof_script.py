from pathlib import Path

from app.db.proof import BACKEND, ROOT, proof_commands


def test_postgres_proof_commands_without_seed() -> None:
    """Build a non-seeding proof workflow for an already prepared database."""
    commands = proof_commands(seed="none", integration=False, skip_start=True)

    labels = [label for label, _, _, _ in commands]

    assert labels == ["run migrations", "check roles", "smoke test"]
    assert all(isinstance(cwd, Path) for _, _, cwd, _ in commands)
    assert commands[0][2] == BACKEND


def test_postgres_proof_commands_with_seed_and_integration() -> None:
    """Build the full local proof workflow with seed and integration checks."""
    commands = proof_commands(seed="local", integration=True, skip_start=False)

    labels = [label for label, _, _, _ in commands]

    assert labels == [
        "start postgres",
        "run migrations",
        "check roles",
        "seed local",
        "smoke test",
        "integration test",
    ]
    assert commands[0][2] == ROOT
    assert commands[-1][3]["VELLUM_RUN_POSTGRES_INTEGRATION"] == "1"
