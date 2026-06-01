from app.config import Settings
from app.db.smoke import run_postgres_smoke, smoke_passed


def test_postgres_smoke_stops_when_database_checks_fail(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.db.smoke.run_database_checks",
        lambda _settings: [
            _db_check("admin", False, "password authentication failed"),
        ],
    )

    results = run_postgres_smoke(Settings())

    assert smoke_passed(results) is False
    assert results[0].name == "db:admin"
    assert results[0].passed is False
    assert results[-1].name == "db:ready"


def test_postgres_smoke_checks_counts_and_executes_queries(monkeypatch, health_uk_catalogue) -> None:
    executed_metrics = []

    monkeypatch.setattr(
        "app.db.smoke.run_database_checks",
        lambda _settings: [
            _db_check("admin", True, "connected"),
            _db_check("seeder", True, "connected"),
            _db_check("readonly", True, "connected"),
            _db_check("auditor", True, "connected"),
        ],
    )
    monkeypatch.setattr(
        "app.db.smoke.load_catalogue",
        lambda _root, _name: health_uk_catalogue,
    )
    monkeypatch.setattr("app.db.smoke.create_engine", lambda _url: FakeEngine())

    def fake_execute_postgres_query(build_result, database_url):
        executed_metrics.append(build_result.provenance.metric_id)
        return FakeExecutionResult(row_count=1, mode="postgres")

    monkeypatch.setattr(
        "app.db.smoke.execute_postgres_query",
        fake_execute_postgres_query,
    )

    results = run_postgres_smoke(Settings(readonly_database_url="postgresql+psycopg://readonly"))

    assert smoke_passed(results) is True
    assert "query:loss_ratio" in {result.name for result in results}
    assert "query:paid_claims" in {result.name for result in results}
    assert "query:decline_rate" in {result.name for result in results}
    assert executed_metrics == ["loss_ratio", "paid_claims", "decline_rate"]


def _db_check(name: str, passed: bool, message: str):
    from app.db.checks import DatabaseCheck

    return DatabaseCheck(name=name, passed=passed, message=message)


class FakeScalarResult:
    def scalar_one(self) -> int:
        return 1


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, _statement):
        return FakeScalarResult()


class FakeEngine:
    def connect(self):
        return FakeConnection()


class FakeExecutionResult:
    def __init__(self, row_count: int, mode: str) -> None:
        self.row_count = row_count
        self.mode = mode
