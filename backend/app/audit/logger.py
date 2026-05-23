import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from app.analytics.models import AnalyticsRequest, QueryBuildResult


@dataclass(frozen=True)
class AuditEvent:
    """One append-only audit event for a user-visible operation."""

    query_id: str
    event_type: str
    created_at: datetime
    request: dict[str, object]
    metric_id: str
    sql: str
    parameters: dict[str, object]
    provenance: dict[str, object]
    validation: dict[str, object]
    execution: dict[str, object] | None = None


class JsonlAuditLogger:
    """Write audit events to a local JSON Lines file for development."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def record(self, event: AuditEvent) -> None:
        """Append one event to the JSONL audit log."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), default=_json_default))
            handle.write("\n")

    def find_by_query_id(self, query_id: str) -> dict[str, object] | None:
        """Return one audit event by query ID from the local JSONL log."""
        if not self.path.exists():
            return None

        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("query_id") == query_id:
                    return event

        return None


def build_preview_audit_event(
    request: AnalyticsRequest,
    result: QueryBuildResult,
) -> AuditEvent:
    """Create an audit event for a successful deterministic query preview."""
    return _build_audit_event(request, result, event_type="query_preview")


def build_execution_audit_event(
    request: AnalyticsRequest,
    result: QueryBuildResult,
    row_count: int,
    answer: str,
) -> AuditEvent:
    """Create an audit event for a successful local demo execution."""
    return _build_audit_event(
        request,
        result,
        event_type="query_execute",
        execution={"mode": "local_demo", "row_count": row_count, "answer": answer},
    )


def _build_audit_event(
    request: AnalyticsRequest,
    result: QueryBuildResult,
    event_type: str,
    execution: dict[str, object] | None = None,
) -> AuditEvent:
    return AuditEvent(
        query_id=f"q_{uuid4().hex}",
        event_type=event_type,
        created_at=datetime.now(UTC),
        request=request.model_dump(),
        metric_id=result.provenance.metric_id,
        sql=result.query.sql,
        parameters=result.query.parameters,
        provenance={
            "metric_version": result.provenance.metric_version,
            "formula": result.provenance.formula,
            "time_anchor": result.provenance.time_anchor,
            "tables_used": list(result.provenance.tables_used),
            "joins_used": list(result.provenance.joins_used),
            "result_shape": {
                "columns": list(result.provenance.result_shape.columns),
                "grain": result.provenance.result_shape.grain,
            },
        },
        validation={
            "passed": result.validation.passed,
            "rules_checked": list(result.validation.rules_checked),
            "rejections": [
                {"rule": item.rule, "message": item.message}
                for item in result.validation.rejections
            ],
        },
        execution=execution,
    )


def _json_default(value: object) -> str:
    if isinstance(value, date | datetime):
        return value.isoformat()
    return str(value)
