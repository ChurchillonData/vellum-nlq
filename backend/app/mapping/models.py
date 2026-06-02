from pydantic import BaseModel, ConfigDict, Field, model_validator


class ColumnMapping(BaseModel):
    """One source column mapped onto one canonical Vellum column."""

    model_config = ConfigDict(extra="forbid")

    canonical_column: str
    source_column: str
    transform: str | None = None


class TableMapping(BaseModel):
    """One source table mapped onto one canonical Vellum table."""

    model_config = ConfigDict(extra="forbid")

    canonical_table: str
    source_table: str
    columns: list[ColumnMapping] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_columns(self) -> "TableMapping":
        columns = [column.canonical_column for column in self.columns]
        if len(columns) != len(set(columns)):
            raise ValueError(
                f"duplicate canonical column in mapping for {self.canonical_table}"
            )
        return self


class SchemaMapping(BaseModel):
    """A partner schema mapped to a Vellum semantic catalogue."""

    model_config = ConfigDict(extra="forbid")

    partner: str
    catalogue: str
    version: str
    tables: list[TableMapping] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_tables(self) -> "SchemaMapping":
        tables = [table.canonical_table for table in self.tables]
        if len(tables) != len(set(tables)):
            raise ValueError("duplicate canonical table in schema mapping")
        return self


class MappingCoverage(BaseModel):
    """Coverage summary for a validated partner schema mapping."""

    model_config = ConfigDict(extra="forbid")

    partner: str
    catalogue: str
    mapped_tables: int
    total_tables: int
    mapped_columns: int
    total_columns: int
    missing_tables: list[str]
    missing_columns: list[str]
