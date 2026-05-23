from pathlib import Path

from app.config import Settings
from app.seeds import loader
from app.seeds.synthetic import build_seed_data


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_settings_define_distinct_local_postgres_roles() -> None:
    settings = Settings()

    assert "vellum_admin" in settings.database_url
    assert "vellum_seeder" in settings.seed_database_url
    assert "vellum_readonly" in settings.readonly_database_url
    assert "vellum_auditor" in settings.audit_database_url


def test_local_postgres_init_creates_separated_roles() -> None:
    sql = (REPO_ROOT / "database" / "init" / "001_roles.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE ROLE vellum_seeder LOGIN" in sql
    assert "CREATE ROLE vellum_readonly LOGIN" in sql
    assert "CREATE ROLE vellum_auditor LOGIN" in sql
    assert "statement_timeout" in sql
    assert "work_mem" in sql
    assert "GRANT CONNECT ON DATABASE vellum" in sql


def test_first_migration_grants_local_role_permissions() -> None:
    migration = (
        REPO_ROOT
        / "backend"
        / "migrations"
        / "versions"
        / "0001_create_claims_schema.py"
    ).read_text(encoding="utf-8")

    assert "GRANT SELECT ON ALL TABLES IN SCHEMA public TO vellum_readonly" in migration
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public" in migration
    assert "ix_claims_incurred_date" in migration
    assert "ix_claim_lines_paid_date" in migration
    assert "ix_premium_coverage_month" in migration


def test_audit_migration_grants_append_only_permissions() -> None:
    migration = (
        REPO_ROOT
        / "backend"
        / "migrations"
        / "versions"
        / "0002_create_audit_events.py"
    ).read_text(encoding="utf-8")

    assert "op.create_table" in migration
    assert '"audit_events"' in migration
    assert "GRANT SELECT, INSERT ON TABLE audit_events TO vellum_auditor" in migration
    assert "UPDATE" not in migration
    assert "DELETE" not in migration


def test_seed_script_uses_seed_database_url(monkeypatch) -> None:
    captured = {}

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, rows=None):
            return None

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    def fake_create_engine(url):
        captured["url"] = url
        return FakeEngine()

    monkeypatch.setattr(loader, "create_engine", fake_create_engine)

    loader.load_seed_data(build_seed_data(member_count=2, month_count=1))

    assert "vellum_seeder" in captured["url"]
