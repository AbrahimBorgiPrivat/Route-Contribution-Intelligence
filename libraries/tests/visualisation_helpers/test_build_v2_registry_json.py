import json
import tempfile
from pathlib import Path
import pytest

from libraries.utils.visualization.visualisation_helpers import (
    build_v2_registry_json,
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _write_v2_route_structure(
    base_dir: Path,
    *,
    label: str,
    route_id: str,
    apr: str,
    week: str,
    with_markers: bool = True,
    with_route_geo: bool = True,
):
    week_dir = base_dir / label / route_id / apr / week
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / f"{route_id}.json").write_text(
        json.dumps({"route_id": route_id})
    )
    if with_markers:
        (week_dir / f"{route_id}_markers.geojson").write_text("{}")
    if with_route_geo:
        (week_dir / f"{route_id}_route.geojson").write_text("{}")
    return week_dir


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def test_build_v2_registry_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        _write_v2_route_structure(
            base_dir,
            label="Structured",
            route_id="37000001",
            apr="O18",
            week="U36",
        )
        registry_path = build_v2_registry_json(
            base_dir=str(base_dir)
        )
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert len(registry) == 1
        entry = registry[0]
        assert entry["label"] == "Structured"
        assert entry["route_id"] == "37000001"
        assert entry["APR_profile"] == "O18"
        assert entry["Week_Profile"] == "U36"
        assert entry["route_json"] == (
            "Structured/37000001/O18/U36/37000001.json"
        )

def test_skips_missing_route_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        week_dir = base_dir / "Structured" / "37000001" / "APR" / "Week"
        week_dir.mkdir(parents=True)
        registry_path = build_v2_registry_json(
            base_dir=str(base_dir)
        )
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert registry == []


def test_handles_missing_optional_geojson():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        _write_v2_route_structure(
            base_dir,
            label="Structured",
            route_id="37000001",
            apr="APR",
            week="Week",
            with_markers=False,
            with_route_geo=False,
        )
        registry_path = build_v2_registry_json(
            base_dir=str(base_dir)
        )
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert len(registry) == 1
        entry = registry[0]
        assert entry["markers_geojson"] is None
        assert entry["route_geojson"] is None

def test_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        registry_path = build_v2_registry_json(
            base_dir=str(base_dir)
        )
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert registry == []

def test_missing_base_directory():
    with pytest.raises(FileNotFoundError):
        build_v2_registry_json(base_dir="__does_not_exist__")

def test_multiple_labels_routes_apr_weeks():
    """
    Validate full multi-dimensional traversal:
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        labels = ["Structured", "Unstructured"]
        routes = ["37000001", "37000002"]
        apr_profiles = ["O18", "SE"]
        weeks = ["U36", "U37"]
        for label in labels:
            for route_id in routes:
                for apr in apr_profiles:
                    for week in weeks:
                        _write_v2_route_structure(
                            base_dir,
                            label=label,
                            route_id=route_id,
                            apr=apr,
                            week=week,
                        )
        registry_path = build_v2_registry_json(
            base_dir=str(base_dir)
        )
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert len(registry) == 16
        unique_keys = {
            (
                r["label"],
                r["route_id"],
                r["APR_profile"],
                r["Week_Profile"],
            )
            for r in registry
        }
        assert len(unique_keys) == 16
        sample = next(
            r for r in registry
            if (
                r["label"] == "Structured"
                and r["route_id"] == "37000001"
                and r["APR_profile"] == "O18"
                and r["Week_Profile"] == "U36"
            )
        )
        assert sample["route_json"] == (
            "Structured/37000001/O18/U36/37000001.json"
        )
        assert sample["markers_geojson"] == (
            "Structured/37000001/O18/U36/37000001_markers.geojson"
        )
        assert sample["route_geojson"] == (
            "Structured/37000001/O18/U36/37000001_route.geojson"
        )

if __name__ == "__main__":
    test_build_v2_registry_basic()
    test_skips_missing_route_json()
    test_empty_directory()
    test_missing_base_directory()
    test_multiple_labels_routes_apr_weeks()

