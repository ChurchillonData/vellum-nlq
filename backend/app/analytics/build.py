from app.analytics.models import AnalyticsRequest, QueryBuildResult, QueryProvenance
from app.planner.loss_ratio import build_loss_ratio_plan
from app.semantic.models import Catalogue, JoinEdge
from app.semantic.resolver import resolve_request
from app.sql.generator import generate_loss_ratio_query
from app.sql.guard import validate_sql


def build_query(catalogue: Catalogue, request: AnalyticsRequest) -> QueryBuildResult:
    """Build one deterministic query with provenance and no database execution."""
    resolved = resolve_request(catalogue, request)
    plan = build_loss_ratio_plan(catalogue, resolved)
    query = generate_loss_ratio_query(plan)
    validation = validate_sql(query.sql)
    provenance = QueryProvenance(
        metric_id=plan.metric.id,
        metric_label=plan.metric.label,
        metric_version=plan.metric.version,
        metric_description=plan.metric.description,
        formula=plan.metric.formula.expression,
        time_anchor=plan.metric.time_anchor,
        tables_used=plan.tables,
        joins_used=tuple(_describe_join(join) for join in plan.joins),
        result_shape=plan.result_shape,
    )
    return QueryBuildResult(
        plan=plan,
        query=query,
        provenance=provenance,
        validation=validation,
    )


def _describe_join(join: JoinEdge) -> str:
    return (
        f"{join.left_table}.{join.left_column} = "
        f"{join.right_table}.{join.right_column}"
    )
