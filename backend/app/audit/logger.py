import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from app.analytics.models import AnalyticsRequest, QueryBuildResult
from app.ask.service import AskRequest, AskResult


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


@dataclass(frozen=True)
class AskAuditEvent:
    """One append-only audit event for a product ask request."""

    query_id: str
    event_type: str
    created_at: datetime
    status: str
    request: dict[str, object]
    resolved_request: dict[str, object] | None
    candidates: list[dict[str, object]]
    safety: dict[str, object] | None
    scope: dict[str, object] | None
    metric_id: str | None = None
    sql: str | None = None
    parameters: dict[str, object] | None = None
    provenance: dict[str, object] | None = None
    validation: dict[str, object] | None = None
    execution: dict[str, object] | None = None


class JsonlAuditLogger:
    """Write audit events to a local JSON Lines file for development."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def record(self, event: AuditEvent | AskAuditEvent) -> None:
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
    mode: str = "local_demo",
) -> AuditEvent:
    """Create an audit event for a successful local demo execution."""
    return _build_audit_event(
        request,
        result,
        event_type="query_execute",
        execution={"mode": mode, "row_count": row_count, "answer": answer},
    )


def build_ask_audit_event(
    request: AskRequest,
    result: AskResult,
) -> AskAuditEvent:
    """Create an audit event for any product ask outcome."""
    return AskAuditEvent(
        query_id=f"q_{uuid4().hex}",
        event_type="ask",
        created_at=datetime.now(UTC),
        status=result.status,
        request={
            "question": request.question,
            "metric_id": request.metric_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "plan_tier": request.plan_tier,
            "group_by": list(request.group_by),
        },
        resolved_request=_resolved_request_payload(result),
        candidates=[
            {
                "metric_id": candidate.metric_id,
                "label": candidate.label,
                "confidence": candidate.confidence,
                "reason": candidate.reason,
            }
            for candidate in result.resolution.candidates
        ],
        safety=_safety_payload(result),
        scope=_scope_payload(result),
        metric_id=_metric_id(result),
        sql=(result.build_result.query.sql if result.build_result is not None else None),
        parameters=(
            result.build_result.query.parameters
            if result.build_result is not None
            else None
        ),
        provenance=(
            _provenance_payload(result.build_result)
            if result.build_result is not None
            else None
        ),
        validation=(
            _validation_payload(result.build_result)
            if result.build_result is not None
            else None
        ),
        execution=(
            {
                "mode": result.execution_result.mode,
                "row_count": result.execution_result.row_count,
                "answer": result.execution_result.answer,
            }
            if result.execution_result is not None
            else None
        ),
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
        provenance=_provenance_payload(result),
        validation=_validation_payload(result),
        execution=execution,
    )


def _resolved_request_payload(result: AskResult) -> dict[str, object] | None:
    request = result.resolution.resolved_request
    if request is None:
        return None
    return request.model_dump()


def _safety_payload(result: AskResult) -> dict[str, object] | None:
    safety = result.resolution.safety
    if safety is None:
        return None
    return {
        "rule_id": safety.rule_id,
        "severity": safety.severity,
        "reason": safety.reason,
    }


def _scope_payload(result: AskResult) -> dict[str, object] | None:
    scope = result.resolution.scope
    if scope is None:
        return None
    return {"reason_id": scope.reason_id, "reason": scope.reason}


def _metric_id(result: AskResult) -> str | None:
    request = result.resolution.resolved_request
    if request is not None:
        return request.metric_id
    if result.resolution.candidates:
        return result.resolution.candidates[0].metric_id
    return None


def _provenance_payload(result: QueryBuildResult) -> dict[str, object]:
    return {
        "metric_version": result.provenance.metric_version,
        "formula": result.provenance.formula,
        "time_anchor": result.provenance.time_anchor,
        "tables_used": list(result.provenance.tables_used),
        "joins_used": list(result.provenance.joins_used),
        "result_shape": {
            "columns": list(result.provenance.result_shape.columns),
            "grain": result.provenance.result_shape.grain,
            "max_rows": result.provenance.result_shape.max_rows,
        },
    }


def _validation_payload(result: QueryBuildResult) -> dict[str, object]:
    return {
        "passed": result.validation.passed,
        "rules_checked": list(result.validation.rules_checked),
        "rejections": [
            {"rule": item.rule, "message": item.message}
            for item in result.validation.rejections
        ],
    }


def _json_default(value: object) -> str:
    if isinstance(value, date | datetime):
        return value.isoformat()
    return str(value)
