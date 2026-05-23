from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionDatasetSummary:
    """Small description of the dataset or database used for execution."""

    name: str
    member_count: int | None
    claim_count: int | None
    premium_row_count: int | None


@dataclass(frozen=True)
class ExecutionResult:
    """Rows and summary produced by a guarded execution path."""

    rows: list[dict[str, object]]
    row_count: int
    answer: str
    dataset: ExecutionDatasetSummary
    mode: str
