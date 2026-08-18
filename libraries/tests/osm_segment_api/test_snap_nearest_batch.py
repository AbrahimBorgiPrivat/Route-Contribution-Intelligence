from typing import List, Dict
from libraries.classes.osm_segment_api import OSMSegmentClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

POINTS: List[Dict[str, float]] = [
    {"x": 863994, "y": 6123307},
    {"x": 863973, "y": 6123314},
    {"x": 863956, "y": 6123159},
]

def test_snap_nearest_batch_local_basic() -> None:
    """
    Integration test for OSMSegmentClient.snap_nearest_batch (local service).

    Covers:
    - basic batch snapping
    - allowed_highways filtering
    - response structure
    - result count consistency
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )
    print("\n=== TEST: OSMSegmentClient.snap_nearest_batch (local) ===")
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:4326",
        allowed_highways={"residential", "secondary", "tertiary"},
    )
    results = client.snap_nearest_batch(
        POINTS,
        show_progress=False,
    )
    assert isinstance(results, list)
    assert len(results) == len(POINTS)
    for i, res in enumerate(results):
        print(f"\n--- Result {i} ---")
        print(res)
        assert "input" in res
        assert "x" in res["input"]
        assert "y" in res["input"]
        assert "segment" in res
        assert "segment_id" in res["segment"]
        assert isinstance(res["segment"]["segment_id"], int)
        assert res["segment"]["segment_id"] > 0
        assert "geometry" in res
        geom = res["geometry"]
        assert "entry_point" in geom
        assert "exit_point" in geom
        assert "side_of_road" in geom
        assert geom["side_of_road"] in {"left", "right", "center", None}
        assert geom["crs"] == "EPSG:4326"

def test_snap_nearest_batch_local_multiple_chunks() -> None:
    """
    Integration test forcing multiple chunks.

    Uses more points than MAX_BATCH_SIZE to verify:
    - chunking logic
    - result aggregation
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )
    print("\n=== TEST: OSMSegmentClient.snap_nearest_batch (chunked) ===")
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:4326",
        allowed_highways={"residential", "secondary", "tertiary"},
    )
    client.MAX_BATCH_SIZE = 2
    points = [
        {"x": POINTS[0]["x"] + i, "y": POINTS[0]["y"] + i}
        for i in range(5)
    ]
    results = client.snap_nearest_batch(
        points,
        show_progress=True,
    )
    assert isinstance(results, list)
    assert len(results) == len(points)


if __name__ == "__main__":
    test_snap_nearest_batch_local_basic()
    test_snap_nearest_batch_local_multiple_chunks()
