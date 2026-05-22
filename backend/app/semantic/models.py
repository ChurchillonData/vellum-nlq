from pydantic import BaseModel, ConfigDict, Field, model_validator


class ColumnSpec(BaseModel):
    """A column exposed by the semantic catalogue."""
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    description: str


class TableSpec(BaseModel):
    """A table that metrics may reference."""
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    columns: list[ColumnSpec]

    @property
    def column_names(self) -> set[str]:
        return {column.name for column in self.columns}


class TablesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tables: list[TableSpec]

    @model_validator(mode="after")
    def reject_duplicate_tables(self) -> "TablesFile":
        names = [table.name for table in self.tables]
        if len(names) != len(set(names)):
            raise ValueError("table names must be unique")
        return self


class JoinEdge(BaseModel):
    """An approved join path between two catalogue tables."""
    model_config = ConfigDict(extra="forbid")

    left_table: str
    left_column: str
    right_table: str
    right_column: str
    cardinality: str


class JoinsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    joins: list[JoinEdge]


class MetricFormula(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numerator: str
    denominator: str | None = None
    expression: str


class MetricSpec(BaseModel):
    """A metric definition loaded from one YAML file."""
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str
    formula: MetricFormula
    required_tables: list[str] = Field(min_length=1)
    time_anchor: str
    currency: str | None = None
    filters_default: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    owner: str
    version: str
    last_reviewed: str

    @property
    def time_anchor_parts(self) -> tuple[str, str]:
        table, separator, column = self.time_anchor.partition(".")
        if not separator or not table or not column:
            raise ValueError("time_anchor must use table.column notation")
        return table, column


class Catalogue(BaseModel):
    """Validated semantic definitions for one line of business."""
    model_config = ConfigDict(extra="forbid")

    name: str
    tables: dict[str, TableSpec]
    joins: list[JoinEdge]
    metrics: dict[str, MetricSpec]
