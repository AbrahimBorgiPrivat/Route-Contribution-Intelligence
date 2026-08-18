from typing import Dict
from libraries.classes.osm_segment_api import OSMSegmentClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


POINT: Dict[str, float] = {
    "x": 863994,
    "y": 6123307,
}


def test_snap_nearest_point_local_basic() -> None:
    """
    Integration test for OSMSegmentClient._snap_nearest_point (local service).

    Covers:
    - basic snapping
    - response structure
    - geometry vectors presence
    - CRS correctness
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM Snap service not running",
    )

    print("\n=== TEST: OSMSegmentClient._snap_nearest_point (local) ===")

    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:4326",
        allowed_highways=["residential", "secondary", "tertiary"],
    )

    res = client._snap_nearest_point(
        x=POINT["x"],
        y=POINT["y"],
    )

    print("\n--- Result ---")
    print(res)

    # --------------------------------------------------
    # Top-level structure
    # --------------------------------------------------
    assert isinstance(res, dict)
    assert "input" in res
    assert "segment" in res
    assert "geometry" in res

    # --------------------------------------------------
    # Input
    # --------------------------------------------------
    inp = res["input"]
    assert "x" in inp
    assert "y" in inp
    assert isinstance(inp["x"], (int, float))
    assert isinstance(inp["y"], (int, float))

    # --------------------------------------------------
    # Segment metadata
    # --------------------------------------------------
    segment = res["segment"]
    assert "segment_id" in segment
    assert isinstance(segment["segment_id"], int)
    assert segment["segment_id"] > 0

    # --------------------------------------------------
    # Geometry
    # --------------------------------------------------
    geom = res["geometry"]
    assert "entry_point" in geom
    assert "exit_point" in geom
    assert "side_of_road" in geom
    assert "crs" in geom

    assert geom["crs"] == "EPSG:4326"
    assert geom["side_of_road"] in {"left", "right", "center", None}

    # --------------------------------------------------
    # Entry / exit points
    # --------------------------------------------------
    entry = geom["entry_point"]
    exit_ = geom["exit_point"]

    for p in (entry, exit_):
        assert "x" in p
        assert "y" in p
        assert "node_id" in p
        assert isinstance(p["x"], (int, float))
        assert isinstance(p["y"], (int, float))
        assert isinstance(p["node_id"], int)

    # --------------------------------------------------
    # NEW: Geometry vectors
    # --------------------------------------------------
    assert "vectors" in geom

    vectors = geom["vectors"]
    assert "entry" in vectors
    assert "exit" in vectors

    for loc in ("entry", "exit"):
        v = vectors[loc]
        assert "tangent" in v
        assert "tangent_hat" in v

        if v["tangent"] is not None:
            assert isinstance(v["tangent"], (list, tuple))
            assert len(v["tangent"]) == 2

        if v["tangent_hat"] is not None:
            assert isinstance(v["tangent_hat"], (list, tuple))
            assert len(v["tangent_hat"]) == 2


if __name__ == "__main__":
    test_snap_nearest_point_local_basic()
