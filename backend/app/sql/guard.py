from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError


SYSTEM_SCHEMAS = {"information_schema", "pg_catalog", "pg_toast"}


@dataclass(frozen=True)
class SqlGuardRejection:
    """One SQL guard rule failure."""

    rule: str
    message: str


@dataclass(frozen=True)
class SqlGuardResult:
    """Validation outcome returned by the SQL guard."""

    passed: bool
    rules_checked: tuple[str, ...]
    rejections: tuple[SqlGuardRejection, ...] = ()


def validate_sql(sql: str) -> SqlGuardResult:
    """Validate the first safe SQL boundary before database execution exists."""
    rules_checked: list[str] = []

    rules_checked.append("comments_absent")
    if _contains_comment(sql):
        return _rejected(
            rules_checked,
            "comments_absent",
            "SQL comments are not allowed in generated queries.",
        )

    rules_checked.append("parseable_sql")
    try:
        statements = [statement for statement in parse(sql, read="postgres") if statement]
    except ParseError as error:
        return _rejected(rules_checked, "parseable_sql", f"SQL parsing failed: {error}")

    rules_checked.append("single_statement")
    if len(statements) != 1:
        return _rejected(
            rules_checked,
            "single_statement",
            "Exactly one SQL statement is allowed.",
        )

    statement = statements[0]
    rules_checked.append("select_only")
    if not isinstance(statement, exp.Select):
        return _rejected(
            rules_checked,
            "select_only",
            "Only SELECT statements are allowed.",
        )

    rules_checked.append("system_schema_absent")
    blocked_schemas = sorted(
        {
            table.db.lower()
            for table in statement.find_all(exp.Table)
            if table.db and table.db.lower() in SYSTEM_SCHEMAS
        }
    )
    if blocked_schemas:
        schema_names = ", ".join(blocked_schemas)
        return _rejected(
            rules_checked,
            "system_schema_absent",
            f"System schema references are not allowed: {schema_names}.",
        )

    return SqlGuardResult(passed=True, rules_checked=tuple(rules_checked))


def _contains_comment(sql: str) -> bool:
    return "--" in sql or "/*" in sql or "*/" in sql


def _rejected(
    rules_checked: list[str],
    rule: str,
    message: str,
) -> SqlGuardResult:
    return SqlGuardResult(
        passed=False,
        rules_checked=tuple(rules_checked),
        rejections=(SqlGuardRejection(rule=rule, message=message),),
    )

