import argparse
from pathlib import Path
from typing import Any

import yaml

from app.mapping.models import MappingCoverage, SchemaMapping
from app.semantic.catalogue import CatalogueError, load_catalogue
from app.semantic.models import Catalogue


class MappingError(ValueError):
    """Raised when a partner schema mapping is invalid."""


def load_schema_mapping(path: Path) -> SchemaMapping:
    """Load one partner schema mapping YAML file."""
    if not path.exists():
        raise MappingError(f"missing schema mapping file: {path}")

    with path.open(encoding="utf-8") as handle:
        data: Any = yaml.safe_load(handle)

    return SchemaMapping.model_validate(data)


def validate_schema_mapping(
    catalogue: Catalogue,
    mapping: SchemaMapping,
) -> MappingCoverage:
    """Validate canonical references and return catalogue coverage."""
    if mapping.catalogue != catalogue.name:
        raise MappingError(
            f"mapping targets catalogue {mapping.catalogue}, expected {catalogue.name}"
        )

    _validate_table_references(catalogue, mapping)
    return build_mapping_coverage(catalogue, mapping)


def build_mapping_coverage(
    catalogue: Catalogue,
    mapping: SchemaMapping,
) -> MappingCoverage:
    """Return mapped table/column counts for one valid schema mapping."""
    mapped_tables = {table.canonical_table for table in mapping.tables}
    mapped_columns = {
        f"{table.canonical_table}.{column.canonical_column}"
        for table in mapping.tables
        for column in table.columns
    }
    catalogue_columns = {
        f"{table.name}.{column.name}"
        for table in catalogue.tables.values()
        for column in table.columns
    }

    return MappingCoverage(
        partner=mapping.partner,
        catalogue=mapping.catalogue,
        mapped_tables=len(mapped_tables),
        total_tables=len(catalogue.tables),
        mapped_columns=len(mapped_columns),
        total_columns=len(catalogue_columns),
        missing_tables=sorted(set(catalogue.tables) - mapped_tables),
        missing_columns=sorted(catalogue_columns - mapped_columns),
    )


def _validate_table_references(catalogue: Catalogue, mapping: SchemaMapping) -> None:
    for table_mapping in mapping.tables:
        table = catalogue.tables.get(table_mapping.canonical_table)
        if table is None:
            raise MappingError(
                f"mapping references unknown canonical table: "
                f"{table_mapping.canonical_table}"
            )

        for column_mapping in table_mapping.columns:
            if column_mapping.canonical_column not in table.column_names:
                raise MappingError(
                    f"mapping references unknown canonical column: "
                    f"{table_mapping.canonical_table}.{column_mapping.canonical_column}"
                )


def parse_args() -> argparse.Namespace:
    """Parse partner schema mapping validation options."""
    parser = argparse.ArgumentParser(description="Validate a partner schema mapping.")
    parser.add_argument("mapping_path", type=Path)
    parser.add_argument("--catalogue", default="health-uk")
    parser.add_argument("--catalogue-root", type=Path)
    return parser.parse_args()


def main() -> None:
    """Validate a partner mapping file and print coverage."""
    args = parse_args()
    catalogue_root = args.catalogue_root or Path(__file__).resolve().parents[2] / "catalogues"

    try:
        catalogue = load_catalogue(catalogue_root, args.catalogue)
        mapping = load_schema_mapping(args.mapping_path)
        coverage = validate_schema_mapping(catalogue, mapping)
    except (CatalogueError, MappingError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(
        f"Mapping {coverage.partner} -> {coverage.catalogue} is valid: "
        f"{coverage.mapped_tables}/{coverage.total_tables} tables, "
        f"{coverage.mapped_columns}/{coverage.total_columns} columns mapped."
    )

    if coverage.missing_tables:
        print("Missing tables:")
        for table_name in coverage.missing_tables:
            print(f"  {table_name}")


if __name__ == "__main__":
    main()
