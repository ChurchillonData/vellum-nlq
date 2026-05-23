from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.semantic.models import Catalogue
from app.sql.guard_catalogue import (
    cte_names,
    disallowed_functions,
    unknown_tables,
    validate_columns,
    validate_physical_joins,
)


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


MAX_GROUPED_RESULT_ROWS = 50


def validate_sql(
    sql: str,
    catalogue: Catalogue,
    parameters: dict[str, object] | None = None,
) -> SqlGuardResult:
    """Validate generated SQL against safety and catalogue rules."""
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

    internal_table_names = cte_names(statement)

    rules_checked.append("table_allowlist")
    table_names = unknown_tables(statement, catalogue, internal_table_names)
    if table_names:
        return _rejected(
            rules_checked,
            "table_allowlist",
            f"Unknown table references are not allowed: {', '.join(table_names)}.",
        )

    rules_checked.append("column_allowlist")
    column_rejection = validate_columns(statement, catalogue, internal_table_names)
    if column_rejection:
        return _rejected(rules_checked, "column_allowlist", column_rejection)

    rules_checked.append("function_allowlist")
    function_names = disallowed_functions(statement)
    if function_names:
        return _rejected(
            rules_checked,
            "function_allowlist",
            "Disallowed SQL functions are not allowed: "
            f"{', '.join(function_names)}.",
        )

    rules_checked.append("parameter_literal_enforcement")
    literal_rejection = _literal_rejection(statement)
    if literal_rejection:
        return _rejected(
            rules_checked,
            "parameter_literal_enforcement",
            literal_rejection,
        )

    rules_checked.append("join_allowlist")
    join_rejection = validate_physical_joins(
        statement,
        catalogue,
        internal_table_names,
    )
    if join_rejection:
        return _rejected(rules_checked, "join_allowlist", join_rejection)

    rules_checked.append("result_size_control")
    result_size_rejection = _result_size_rejection(statement, parameters or {})
    if result_size_rejection:
        return _rejected(
            rules_checked,
            "result_size_control",
            result_size_rejection,
        )

    return SqlGuardResult(passed=True, rules_checked=tuple(rules_checked))


def _contains_comment(sql: str) -> bool:
    return "--" in sql or "/*" in sql or "*/" in sql


def _literal_rejection(statement: exp.Expression) -> str | None:
    for literal in statement.find_all(exp.Literal):
        if literal.is_string:
            return "String and date values must be supplied as bound parameters."
    return None


def _result_size_rejection(
    statement: exp.Expression,
    parameters: dict[str, object],
) -> str | None:
    if statement.args.get("group") is None:
        return None

    limit = statement.args.get("limit")
    if limit is None:
        return "Grouped result sets must include an explicit row limit."

    limit_value = _limit_value(limit, parameters)
    if limit_value is None:
        return "Grouped result limit must be a known integer value."
    if limit_value > MAX_GROUPED_RESULT_ROWS:
        return (
            "Grouped result limit exceeds the maximum allowed rows: "
            f"{MAX_GROUPED_RESULT_ROWS}."
        )

    return None


def _limit_value(
    limit: exp.Expression,
    parameters: dict[str, object],
) -> int | None:
    expression = limit.expression
    if isinstance(expression, exp.Literal) and not expression.is_string:
        return int(expression.this)
    if isinstance(expression, exp.Placeholder):
        parameter_name = expression.this.name
        value = parameters.get(parameter_name)
        return int(value) if isinstance(value, int) else None
    return None


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
