from pathlib import Path

import pytest

from app.mapping.models import ColumnMapping, SchemaMapping, TableMapping
from app.mapping.validator import (
    MappingError,
    load_schema_mapping,
    validate_schema_mapping,
)


def test_example_partner_mapping_covers_health_uk_catalogue(health_uk_catalogue) -> None:
    mapping_path = (
        Path(__file__).resolve().parents[2]
        / "mappings"
        / "health-uk"
        / "example_insurer.yaml"
    )

    mapping = load_schema_mapping(mapping_path)
    coverage = validate_schema_mapping(health_uk_catalogue, mapping)

    assert coverage.partner == "example-insurer"
    assert coverage.catalogue == "health-uk"
    assert coverage.mapped_tables == coverage.total_tables
    assert coverage.mapped_columns == coverage.total_columns
    assert coverage.missing_tables == []
    assert coverage.missing_columns == []


def test_mapping_rejects_wrong_catalogue(health_uk_catalogue) -> None:
    mapping = SchemaMapping(
        partner="example-insurer",
        catalogue="motor-uk",
        version="0.1.0",
        tables=[
            TableMapping(
                canonical_table="claims",
                source_table="claim_header",
                columns=[
                    ColumnMapping(
                        canonical_column="id",
                        source_column="claim_id",
                    )
                ],
            )
        ],
    )

    with pytest.raises(MappingError, match="expected health-uk"):
        validate_schema_mapping(health_uk_catalogue, mapping)


def test_mapping_rejects_unknown_canonical_table(health_uk_catalogue) -> None:
    mapping = SchemaMapping(
        partner="example-insurer",
        catalogue="health-uk",
        version="0.1.0",
        tables=[
            TableMapping(
                canonical_table="unknown_table",
                source_table="claim_header",
                columns=[
                    ColumnMapping(
                        canonical_column="id",
                        source_column="claim_id",
                    )
                ],
            )
        ],
    )

    with pytest.raises(MappingError, match="unknown canonical table"):
        validate_schema_mapping(health_uk_catalogue, mapping)


def test_mapping_rejects_unknown_canonical_column(health_uk_catalogue) -> None:
    mapping = SchemaMapping(
        partner="example-insurer",
        catalogue="health-uk",
        version="0.1.0",
        tables=[
            TableMapping(
                canonical_table="claims",
                source_table="claim_header",
                columns=[
                    ColumnMapping(
                        canonical_column="unknown_column",
                        source_column="claim_id",
                    )
                ],
            )
        ],
    )

    with pytest.raises(MappingError, match="unknown canonical column"):
        validate_schema_mapping(health_uk_catalogue, mapping)
