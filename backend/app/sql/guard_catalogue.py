from sqlglot import exp

from app.semantic.models import Catalogue, JoinEdge


ALLOWED_FUNCTIONS = {"CAST", "NULLIF", "SUM"}
IGNORED_FUNCTION_NODES = (exp.And, exp.Or, exp.Not)


def cte_names(statement: exp.Expression) -> set[str]:
    """Return names introduced by common table expressions."""
    return {cte.alias_or_name for cte in statement.find_all(exp.CTE)}


def unknown_tables(
    statement: exp.Expression,
    catalogue: Catalogue,
    internal_table_names: set[str],
) -> list[str]:
    """Return physical table names not declared by the catalogue."""
    return sorted(
        {
            table.name
            for table in statement.find_all(exp.Table)
            if table.name not in catalogue.tables
            and table.name not in internal_table_names
        }
    )


def validate_columns(
    statement: exp.Expression,
    catalogue: Catalogue,
    internal_table_names: set[str],
) -> str | None:
    """Validate physical column references against catalogue table columns."""
    if next(statement.find_all(exp.Star), None):
        return "Wildcard column references are not allowed."

    for column in statement.find_all(exp.Column):
        table_name = column.table
        if table_name in internal_table_names:
            continue
        if not table_name:
            return f"Column {column.name} must include its table name."

        table = catalogue.tables.get(table_name)
        if table is None:
            continue
        if column.name not in table.column_names:
            return f"Unknown column reference: {table_name}.{column.name}."

    return None


def disallowed_functions(statement: exp.Expression) -> list[str]:
    """Return SQL function names outside the current guard allowlist."""
    names: set[str] = set()
    for function in statement.find_all(exp.Func):
        if isinstance(function, IGNORED_FUNCTION_NODES):
            continue

        function_name = _function_name(function)
        if function_name not in ALLOWED_FUNCTIONS:
            names.add(function_name)

    return sorted(names)


def validate_physical_joins(
    statement: exp.Expression,
    catalogue: Catalogue,
    internal_table_names: set[str],
) -> str | None:
    """Validate physical-table joins against approved catalogue edges."""
    approved_joins = {_join_signature(join) for join in catalogue.joins}

    for join in statement.find_all(exp.Join):
        joined_table = join.this
        if not isinstance(joined_table, exp.Table):
            continue
        if joined_table.name in internal_table_names:
            continue

        predicates = _join_predicate_signatures(join)
        if not predicates:
            return f"Join to {joined_table.name} must use a column equality predicate."
        if not predicates & approved_joins:
            return f"Join to {joined_table.name} is not approved by the catalogue."

    return None


def _function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return function.name.upper()
    return function.sql_name().upper()


def _join_signature(join: JoinEdge) -> frozenset[tuple[str, str]]:
    return frozenset(
        {
            (join.left_table, join.left_column),
            (join.right_table, join.right_column),
        }
    )


def _join_predicate_signatures(join: exp.Join) -> set[frozenset[tuple[str, str]]]:
    on_expression = join.args.get("on")
    if on_expression is None:
        return set()

    signatures: set[frozenset[tuple[str, str]]] = set()
    for predicate in on_expression.find_all(exp.EQ):
        left_column = predicate.left
        right_column = predicate.right
        if not isinstance(left_column, exp.Column) or not isinstance(
            right_column, exp.Column
        ):
            continue
        if not left_column.table or not right_column.table:
            continue

        signatures.add(
            frozenset(
                {
                    (left_column.table, left_column.name),
                    (right_column.table, right_column.name),
                }
            )
        )

    return signatures

