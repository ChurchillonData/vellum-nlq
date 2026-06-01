from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.db.checks import all_checks_passed, run_database_checks


def test_database_checks_report_success(monkeypatch) -> None:
    captured_urls = []

    class FakeResult:
        def scalar_one(self) -> str:
            return "vellum_test"

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, _statement):
            return FakeResult()

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    def fake_create_engine(url: str, **_kwargs):
        captured_urls.append(url)
        return FakeEngine()

    monkeypatch.setattr("app.db.checks.create_engine", fake_create_engine)

    checks = run_database_checks(
        Settings(
            database_url="postgresql+psycopg://admin",
            seed_database_url="postgresql+psycopg://seed",
            readonly_database_url="postgresql+psycopg://readonly",
            audit_database_url="postgresql+psycopg://audit",
        )
    )

    assert all_checks_passed(checks) is True
    assert [check.name for check in checks] == ["admin", "seeder", "readonly", "auditor"]
    assert [check.message for check in checks] == ["connected as vellum_test"] * 4
    assert captured_urls == [
        "postgresql+psycopg://admin",
        "postgresql+psycopg://seed",
        "postgresql+psycopg://readonly",
        "postgresql+psycopg://audit",
    ]


def test_database_checks_report_authentication_failure(monkeypatch) -> None:
    class FakeEngine:
        def connect(self):
            raise OperationalError(
                "select 1",
                {},
                Exception("password authentication failed for user"),
            )

    monkeypatch.setattr("app.db.checks.create_engine", lambda *_args, **_kwargs: FakeEngine())

    checks = run_database_checks()

    assert all_checks_passed(checks) is False
    assert checks[0].passed is False
    assert checks[0].message == "password authentication failed"
