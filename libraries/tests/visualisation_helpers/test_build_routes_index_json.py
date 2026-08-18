import json
import pytest
from libraries.utils.visualization.visualisation_helpers import build_routes_index_json

KPI_MAPPING = [
    {"name": "Rute ID", "key": "route_id"},
    {"name": "T1 DG (best)", "key": "t1_DG_best"},
    {"name": "T1 Outliers", "key": "t1_seg_outliers"},
    {"name": "T2 DG (best)", "key": "t2_DG_best"},
    {"name": "T2 Outliers", "key": "t2_seg_outliers"},
]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _write_route_json(base_dir, route_id, content=None):
    """Create application/data/routes/<route_id>/<route_id>.json"""
    route_dir = base_dir / "routes" / route_id
    route_dir.mkdir(parents=True, exist_ok=True)
    if content is None:
        content = {"route_id": route_id}
    path = route_dir / f"{route_id}.json"
    path.write_text(json.dumps(content))
    return path


# ------------------------------------------------------------------
# Tests: use_data = True (pipeline-driven)
# ------------------------------------------------------------------
def test_build_routes_index_use_data(tmp_path):
    base_dir = tmp_path / "application" / "data"
    base_dir.mkdir(parents=True)
    route_json = _write_route_json(base_dir, "37000001")
    route_outputs = [
        {
            "route_id": "37000001",
            "index": str(route_json),
        }
    ]
    index_path = build_routes_index_json(
        base_dir=str(base_dir),
        kpi_mapping=KPI_MAPPING,
        use_data=True,
        route_outputs=route_outputs,
    )
    index_data = json.loads(open(index_path, encoding="utf-8").read())
    assert index_data["kpis"] == KPI_MAPPING
    assert index_data["routes"] == [
        {
            "route_id": "37000001",
            "path": "routes/37000001/37000001.json",
        }
    ]

def test_use_data_requires_route_outputs(tmp_path):
    base_dir = tmp_path / "data"
    base_dir.mkdir()
    with pytest.raises(ValueError):
        build_routes_index_json(
            base_dir=str(base_dir),
            kpi_mapping=KPI_MAPPING,
            use_data=True,
            route_outputs=None,
        )

# ------------------------------------------------------------------
# Tests: use_data = False (filesystem-driven)
# ------------------------------------------------------------------
def test_build_routes_index_scan_filesystem(tmp_path):
    base_dir = tmp_path / "application" / "data"
    base_dir.mkdir(parents=True)
    _write_route_json(base_dir, "37000001")
    _write_route_json(base_dir, "37000002")
    index_path = build_routes_index_json(
        base_dir=str(base_dir),
        kpi_mapping=KPI_MAPPING,
        use_data=False,
    )
    index_data = json.loads(open(index_path, encoding="utf-8").read())
    routes = sorted(index_data["routes"], key=lambda r: r["route_id"])
    assert routes == [
        {
            "route_id": "37000001",
            "path": "routes/37000001/37000001.json",
        },
        {
            "route_id": "37000002",
            "path": "routes/37000002/37000002.json",
        },
    ]
    assert index_data["kpis"] == KPI_MAPPING

def test_scan_skips_missing_route_json(tmp_path):
    base_dir = tmp_path / "data"
    routes_dir = base_dir / "routes"
    routes_dir.mkdir(parents=True)
    (routes_dir / "37000001").mkdir()
    index_path = build_routes_index_json(
        base_dir=str(base_dir),
        kpi_mapping=KPI_MAPPING,
        use_data=False,
    )
    index_data = json.loads(open(index_path, encoding="utf-8").read())
    assert index_data["routes"] == []

def test_scan_skips_invalid_json(tmp_path):
    base_dir = tmp_path / "data"
    route_dir = base_dir / "routes" / "37000001"
    route_dir.mkdir(parents=True)
    (route_dir / "37000001.json").write_text("{ not valid json")
    index_path = build_routes_index_json(
        base_dir=str(base_dir),
        kpi_mapping=KPI_MAPPING,
        use_data=False,
    )
    index_data = json.loads(open(index_path, encoding="utf-8").read())
    assert index_data["routes"] == []


def test_scan_requires_routes_directory(tmp_path):
    base_dir = tmp_path / "data"
    base_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        build_routes_index_json(
            base_dir=str(base_dir),
            kpi_mapping=KPI_MAPPING,
            use_data=False,
        )

if __name__ == "__main__":
    test_build_routes_index_use_data()
    test_use_data_requires_route_outputs()
    test_build_routes_index_scan_filesystem()
    test_scan_skips_missing_route_json()
    test_scan_skips_invalid_json()
    test_scan_requires_routes_directory()