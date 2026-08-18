from __future__ import annotations
import os

os.environ["OSM_SNAP_BUILD_DIR"] = "services/osm/data/build"
os.environ["OSM_SNAP_LAZY_TREES"] = "false"

import pytest
from typing import Iterator
from fastapi.testclient import TestClient
from services.osm.app.main import app
from services.osm.app.runtime.loader import OSMSnapIndexLoader
from services.osm.app.runtime.index import OSMSnapIndex

# --------------------------------------------------
# FastAPI test client (API tests)
# --------------------------------------------------
@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """
    FastAPI TestClient with real application and real snap index.

    Used by tests in:
      - services/osm/tests/api
    """
    os.environ.setdefault("OSM_SNAP_BUILD_DIR", "services/osm/data/build")
    os.environ.setdefault("OSM_SNAP_LAZY_TREES", "false")

    with TestClient(app) as client:
        yield client

# --------------------------------------------------
# Direct snap index fixture (integration / unit tests)
# --------------------------------------------------
@pytest.fixture(scope="session")
def snap_index() -> OSMSnapIndex:
    """
    Load snap index once for integration and unit tests.

    Used by tests in:
      - services/osm/tests/integration
      - services/osm/tests/unit
    """
    loader = OSMSnapIndexLoader(
        build_dir=os.environ.get("OSM_SNAP_BUILD_DIR", "services/osm/data/build"),
        lazy_trees=False,
    )
    state = loader.load()
    return OSMSnapIndex(state)