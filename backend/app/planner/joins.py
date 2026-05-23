from app.semantic.models import Catalogue, JoinEdge


class PlanningError(ValueError):
    """Raised when a requested plan cannot be built from catalogue joins."""


def find_join(catalogue: Catalogue, left_table: str, right_table: str) -> JoinEdge:
    """Find an approved join between two catalogue tables."""
    for join in catalogue.joins:
        tables = {join.left_table, join.right_table}
        if tables == {left_table, right_table}:
            return join

    raise PlanningError(f"missing approved join between {left_table} and {right_table}")

