from pathlib import Path

import pytest

from app.semantic.catalogue import load_catalogue
from app.semantic.models import Catalogue


@pytest.fixture
def health_uk_catalogue() -> Catalogue:
    """Load the catalogue used by focused backend tests."""
    catalogue_root = Path(__file__).resolve().parents[1] / "catalogues"
    return load_catalogue(catalogue_root, "health-uk")
