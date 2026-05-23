import json
from datetime import date, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from sqlalchemy import create_engine, insert, select

from app.audit.logger import (
    AskAuditEvent,
    AuditEvent,
    audit_event_to_record,
)
from app.config import Settings
from app.db.schema import audit_events


class AuditStore(Protocol):
    """Append-only audit event storage."""

    def record(self, event: AuditEvent | AskAuditEvent) -> None:
        """Persist one audit event."""
        ...

    def find_by_query_id(self, query_id: str) -> dict[str, object] | None:
        """Return one audit event by query ID."""
        ...


class JsonlAuditStore:
    """Write audit events to a local JSON Lines file for development."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def record(self, event: AuditEvent | AskAuditEvent) -> None:
        """Append one event to the JSONL audit log."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(audit_event_to_record(event), default=_json_default))
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


class PostgresAuditStore:
    """Append audit events to the Postgres audit table."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)

    def record(self, event: AuditEvent | AskAuditEvent) -> None:
        """Append one event to Postgres."""
        record = _json_safe_record(audit_event_to_record(event))
        with self.engine.begin() as connection:
            connection.execute(
                insert(audit_events),
                {
                    "id": uuid4(),
                    "query_id": event.query_id,
                    "event_type": event.event_type,
                    "created_at": event.created_at,
                    "payload": record,
                },
            )

    def find_by_query_id(self, query_id: str) -> dict[str, object] | None:
        """Return one event from Postgres by query ID."""
        statement = select(audit_events.c.payload).where(
            audit_events.c.query_id == query_id
        )
        with self.engine.connect() as connection:
            row = connection.execute(statement).first()

        if row is None:
            return None
        return dict(row._mapping["payload"])


def build_audit_store(settings: Settings) -> AuditStore:
    """Create the configured audit store."""
    if settings.audit_backend == "postgres":
        return PostgresAuditStore(settings.audit_database_url)
    return JsonlAuditStore(settings.audit_log_path)


def _json_safe_record(record: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(record, default=_json_default))


def _json_default(value: object) -> str:
    if isinstance(value, date | datetime):
        return value.isoformat()
    return str(value)
