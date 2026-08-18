import pytest
from libraries.classes.osm_segment_api import OSMSegmentClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

POINT = {"x": 863994, "y": 6123307}

def _make_client(highways=None):
    return OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:4326",
        allowed_highways=highways,
    )

def test_group_segments_on_side_local_basic() -> None:
    """
    Integration test for OSMSegmentClient.group_segments_on_side (local service).

    Covers:
    - forward + backward traversal
    - visited segment tracking
    - structural invariants of output
    - no rotation (raw endpoints)
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM snap service not running",
    )
    print("\n=== TEST: group_segments_on_side (basic, no rotation) ===")
    client = _make_client({"residential", "secondary", "tertiary"})
    snap = client.snap_nearest_batch(
        [POINT],
        show_progress=False,
    )[0]
    group = client.group_segments_on_side(
        snap,
        allowed_highways={"residential", "secondary", "tertiary"},
        use_rotated_side=False,
    )
    print(group)

    # --------------------------------------------------
    # Structural checks
    # --------------------------------------------------
    assert isinstance(group, dict)
    for key in (
        "seg_seq_id",
        "site_of_road",
        "visited_segments",
        "segments",
        "start_point",
        "end_point",
    ):
        assert key in group
    segments = group["segments"]
    visited = group["visited_segments"]
    assert isinstance(segments, list)
    assert len(segments) >= 1
    segment_ids = [sid for sid, _ in segments]
    local_indices = [idx for _, idx in segments]
    assert local_indices == list(range(len(segments)))
    assert set(segment_ids) == set(visited)
    assert group["seg_seq_id"] == segment_ids[0]

    # --------------------------------------------------
    # Geometry checks
    # --------------------------------------------------
    start = group["start_point"]
    end = group["end_point"]
    assert "lon" in start and "lat" in start
    assert "lon" in end and "lat" in end
    side = group["site_of_road"]
    if side is not None:
        assert side in {"left", "right"}

def test_group_segments_on_side_no_expansion() -> None:
    """
    Edge-case test:
    grouping may return only the original segment.
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM snap service not running",
    )
    print("\n=== TEST: group_segments_on_side (single segment case) ===")
    client = _make_client({"residential"})
    snap = client.snap_nearest_batch(
        [POINT],
        show_progress=False,
    )[0]
    group = client.group_segments_on_side(
        snap,
        use_rotated_side=False,
    )
    print(group)
    segments = group["segments"]
    assert len(segments) >= 1
    assert segments[0][1] == 0


def test_group_segments_on_side_with_rotated_side() -> None:
    """
    Integration test for rotated side-of-road endpoints.

    Verifies:
    - rotated start/end differ from raw endpoints
    - first/last segment vectors are used
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM snap service not running",
    )
    print("\n=== TEST: group_segments_on_side (rotated side) ===")
    client = _make_client({"residential", "secondary", "tertiary"})
    snap = client.snap_nearest_batch(
        [POINT],
        show_progress=False,
    )[0]
    raw_entry = snap["geometry"]["entry_point"]
    raw_exit = snap["geometry"]["exit_point"]
    group = client.group_segments_on_side(
        snap,
        allowed_highways={"residential", "secondary", "tertiary"},
        use_rotated_side=True,
        offset_m=4.5,
        entry_angle_deg=90.0,
        exit_angle_deg=90.0,
    )
    print(group)
    start = group["start_point"]
    end = group["end_point"]
    assert (
        start["lon"] != raw_entry["x"]
        or start["lat"] != raw_entry["y"]
    )
    assert (
        end["lon"] != raw_exit["x"]
        or end["lat"] != raw_exit["y"]
    )
    side = group["site_of_road"]
    if side is not None:
        assert side in {"left", "right"}

@pytest.mark.parametrize("bad_side", ["center", "up", "", 123])
def test_group_segments_on_side_invalid_side_variants(bad_side):
    """
    Pure unit-level validation of side_of_road parameter.
    """
    client = OSMSegmentClient(base_url="local")
    dummy_seg = {
        "segment": {"segment_id": 1},
        "geometry": {
            "side_of_road": "left",
            "entry_point": {"x": 0.0, "y": 0.0},
            "exit_point": {"x": 1.0, "y": 1.0},
            "vectors": {
                "entry": {"tangent_hat": (1.0, 0.0)},
                "exit": {"tangent_hat": (1.0, 0.0)},
            },
        },
    }
    with pytest.raises(ValueError):
        client.group_segments_on_side(
            dummy_seg,
            side_of_road=bad_side,
        )

if __name__ == "__main__":
    test_group_segments_on_side_local_basic()
    test_group_segments_on_side_no_expansion()
    test_group_segments_on_side_with_rotated_side()
