import argparse
from pathlib import Path
from typing import Any

import yaml

from app.planner.grouping import supported_groupings_for_metric
from app.semantic.models import Catalogue, JoinsFile, MetricSpec, TablesFile, TableSpec


class CatalogueError(ValueError):
    """Raised when catalogue files are missing or internally inconsistent."""


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise CatalogueError(f"missing catalogue file: {path}")

    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_catalogue(root: Path, name: str) -> Catalogue:
    """Load and validate one catalogue directory from YAML files."""
    catalogue_dir = root / name
    tables_file = TablesFile.model_validate(_read_yaml(catalogue_dir / "tables.yaml"))
    joins_file = JoinsFile.model_validate(_read_yaml(catalogue_dir / "joins.yaml"))
    metric_paths = sorted((catalogue_dir / "metrics").glob("*.yaml"))

    if not metric_paths:
        raise CatalogueError(f"catalogue has no metric definitions: {catalogue_dir}")

    tables = {table.name: table for table in tables_file.tables}
    metrics = _load_metrics(metric_paths)

    _validate_join_edges(tables, joins_file)
    _validate_metrics(tables, metrics)

    return Catalogue(
        name=name,
        tables=tables,
        joins=joins_file.joins,
        metrics=metrics,
    )


def _load_metrics(metric_paths: list[Path]) -> dict[str, MetricSpec]:
    metrics: dict[str, MetricSpec] = {}

    for metric_path in metric_paths:
        metric = MetricSpec.model_validate(_read_yaml(metric_path))
        if metric.id in metrics:
            raise CatalogueError(f"duplicate metric id: {metric.id}")
        metrics[metric.id] = metric

    return metrics


def _validate_join_edges(tables: dict[str, TableSpec], joins_file: JoinsFile) -> None:
    for join in joins_file.joins:
        _require_column(tables, join.left_table, join.left_column, "join")
        _require_column(tables, join.right_table, join.right_column, "join")


def _validate_metrics(tables: dict[str, TableSpec], metrics: dict[str, MetricSpec]) -> None:
    for metric in metrics.values():
        for table_name in metric.required_tables:
            if table_name not in tables:
                raise CatalogueError(
                    f"metric {metric.id} requires unknown table {table_name}"
                )

        time_table, time_column = metric.time_anchor_parts
        _require_column(tables, time_table, time_column, f"metric {metric.id} time_anchor")


def _require_column(
    tables: dict[str, TableSpec],
    table_name: str,
    column_name: str,
    source: str,
) -> None:
    table = tables.get(table_name)
    if table is None:
        raise CatalogueError(f"{source} references unknown table {table_name}")
    if column_name not in table.column_names:
        raise CatalogueError(
            f"{source} references unknown column {table_name}.{column_name}"
        )


def parse_args() -> argparse.Namespace:
    """Parse catalogue validation and inspection commands."""
    parser = argparse.ArgumentParser(description="Inspect a Vellum-NLQ catalogue.")
    parser.add_argument("catalogue", nargs="?", default="health-uk")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--list-metrics", action="store_true")
    parser.add_argument("--list-dimensions", action="store_true")
    parser.add_argument("--check-synonyms", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run the small catalogue CLI used by local development commands."""
    args = parse_args()
    root = args.root or Path(__file__).resolve().parents[2] / "catalogues"
    catalogue = load_catalogue(root, args.catalogue)

    if args.list_metrics:
        for metric_id in catalogue.metrics:
            print(metric_id)
        return

    if args.list_dimensions:
        for dimension in supported_dimensions(catalogue):
            print(dimension)
        return

    if args.check_synonyms:
        collisions = synonym_collisions(catalogue)
        if collisions:
            for term, metric_ids in collisions.items():
                print(f"{term}: {', '.join(metric_ids)}")
            raise SystemExit(1)
        print(f"Catalogue {catalogue.name} has no synonym collisions.")
        return

    if args.validate or not any(
        (args.list_metrics, args.list_dimensions, args.check_synonyms)
    ):
        print(
            f"Catalogue {catalogue.name} is valid: "
            f"{len(catalogue.tables)} tables, {len(catalogue.metrics)} metrics."
        )


def supported_dimensions(catalogue: Catalogue) -> list[str]:
    """Return dimensions currently supported by deterministic grouped analytics."""
    dimensions = set()
    for metric_id in catalogue.metrics:
        dimensions.update(supported_groupings_for_metric(metric_id))
    return sorted(dimensions)


def synonym_collisions(catalogue: Catalogue) -> dict[str, list[str]]:
    """Return normalized synonym terms that point to more than one metric."""
    owners: dict[str, list[str]] = {}
    for metric in catalogue.metrics.values():
        terms = [metric.id, metric.label, *metric.synonyms]
        for term in terms:
            normalized = normalize_term(term)
            owners.setdefault(normalized, []).append(metric.id)

    return {
        term: sorted(set(metric_ids))
        for term, metric_ids in owners.items()
        if len(set(metric_ids)) > 1
    }


def normalize_term(term: str) -> str:
    """Normalize metric labels and synonyms for collision checks."""
    return " ".join(term.casefold().replace("_", " ").replace("-", " ").split())


if __name__ == "__main__":
    main()
