import os

import pytest

from app.config import Settings
from app.db.smoke import SmokeResult, run_postgres_smoke, smoke_passed


pytestmark = pytest.mark.skipif(
    os.getenv("VELLUM_RUN_POSTGRES_INTEGRATION") != "1",
    reason="set VELLUM_RUN_POSTGRES_INTEGRATION=1 to run live Postgres tests",
)


def test_seeded_postgres_supports_guarded_execution() -> None:
    """Verify a seeded Postgres database can run guarded catalogue queries."""
    results = run_postgres_smoke(Settings(execution_backend="postgres"))
    failures = [result for result in results if not result.passed]

    assert smoke_passed(results), _format_failures(failures)


def _format_failures(failures: list[SmokeResult]) -> str:
    return "\n".join(
        f"{failure.name}: {failure.message}"
        for failure in failures
    )
