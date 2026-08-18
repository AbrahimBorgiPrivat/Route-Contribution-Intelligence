from libraries.classes.osm_segment_api import OSMSegmentClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

def test_fetch_segment_local_basic() -> None:
    """
    Integration test for OSMSegmentClient.fetch_segment (local service).

    Assumes:
    - local OSM Snap Service is running
    - segment_id exists in the indexed dataset
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )
    print("\n=== TEST: OSMSegmentClient.fetch_segment (local) ===")
    client = OSMSegmentClient(
        base_url="local",
        output_crs="EPSG:4326",
    )
    segment_id = 1
    result = client.fetch_segment(segment_id)
    print("\n--- Segment result ---")
    print(result)

    # --------------------------------------------------
    # Basic structure assertions
    # --------------------------------------------------
    assert isinstance(result, dict)
    assert "segment" in result
    assert "geometry" in result
    segment = result["segment"]
    geometry = result["geometry"]
    assert "segment_id" in segment
    assert segment["segment_id"] == segment_id
    assert "entry_node" in segment
    assert "exit_node" in segment
    assert segment["entry_node"] != segment["exit_node"]
    assert "entry_point" in geometry
    assert "exit_point" in geometry
    assert "x" in geometry["entry_point"]
    assert "y" in geometry["entry_point"]
    assert "x" in geometry["exit_point"]
    assert "y" in geometry["exit_point"]
    assert geometry["crs"] == "EPSG:4326"
    if geometry.get("side_of_road") is not None:
        assert geometry["side_of_road"] in {"left", "right", "center"}


def test_fetch_segment_invalid_id_raises() -> None:
    """
    Invalid segment_id should raise an exception.
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )
    print("\n=== TEST: OSMSegmentClient.fetch_segment (invalid id) ===")
    client = OSMSegmentClient(
        base_url="local",
        output_crs="EPSG:4326",
    )
    invalid_segment_id = -1
    try:
        client.fetch_segment(invalid_segment_id)
        raise AssertionError("Expected fetch_segment to fail for invalid segment_id")
    except Exception as e:
        print("Caught expected exception:")
        print(e)


if __name__ == "__main__":
    test_fetch_segment_local_basic()
    test_fetch_segment_invalid_id_raises()
