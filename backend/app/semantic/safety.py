from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyFinding:
    """A deterministic safety rule triggered by a user question."""

    rule_id: str
    severity: str
    reason: str


DESTRUCTIVE_RULES = {
    "drop": SafetyFinding(
        rule_id="DDL_DROP_PATTERN",
        severity="critical",
        reason="Question contains destructive DROP intent.",
    ),
    "truncate": SafetyFinding(
        rule_id="DDL_TRUNCATE_PATTERN",
        severity="critical",
        reason="Question contains destructive TRUNCATE intent.",
    ),
    "delete": SafetyFinding(
        rule_id="DML_DELETE_PATTERN",
        severity="critical",
        reason="Question contains destructive DELETE intent.",
    ),
    "alter": SafetyFinding(
        rule_id="DDL_ALTER_PATTERN",
        severity="critical",
        reason="Question contains schema mutation intent.",
    ),
    "update": SafetyFinding(
        rule_id="DML_UPDATE_PATTERN",
        severity="high",
        reason="Question contains data mutation intent.",
    ),
    "insert": SafetyFinding(
        rule_id="DML_INSERT_PATTERN",
        severity="high",
        reason="Question contains data insertion intent.",
    ),
}


def classify_question_safety(tokens: set[str]) -> SafetyFinding | None:
    """Return the first safety finding for unsupported database operations."""
    for token in sorted(tokens):
        finding = DESTRUCTIVE_RULES.get(token)
        if finding is not None:
            return finding
    return None

