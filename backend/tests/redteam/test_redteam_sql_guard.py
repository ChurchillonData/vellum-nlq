from pathlib import Path

import yaml

from app.sql.guard import validate_sql


CASES_FILE = Path(__file__).with_name("sql_guard_cases.yaml")


def test_redteam_sql_guard_cases_are_rejected(health_uk_catalogue) -> None:
    """Run unsafe SQL shapes directly through the SQL guard."""
    cases = _load_cases()

    for case in cases:
        result = validate_sql(str(case["sql"]), health_uk_catalogue)

        assert result.passed is False, case["id"]
        assert result.rejections[0].rule == case["expected_rule"], case["id"]


def _load_cases() -> list[dict[str, object]]:
    payload = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    return list(payload["cases"])
