import math
from libraries.classes.osm_segment_api import OSMSegmentClient

def assert_point_close(p, q, eps: float = 1e-6):
    assert abs(p["lon"] - q["lon"]) < eps, f"lon mismatch: {p} != {q}"
    assert abs(p["lat"] - q["lat"]) < eps, f"lat mismatch: {p} != {q}"


def test_side_endpoints_left_basic():
    """
    Simple horizontal segment pointing east.
    Left side should be north (+y).
    """
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:25832",  
    )
    entry_lon, entry_lat = 0.0, 0.0
    exit_lon, exit_lat = 10.0, 0.0
    entry_tangent_hat = (1.0, 0.0)   
    exit_tangent_hat = (1.0, 0.0)    
    offset_m = 5.0
    start, end = client.compute_side_endpoints_from_vectors(
        entry_lon=entry_lon,
        entry_lat=entry_lat,
        exit_lon=exit_lon,
        exit_lat=exit_lat,
        entry_tangent_hat=entry_tangent_hat,
        exit_tangent_hat=exit_tangent_hat,
        side="left",
        offset_m=offset_m,
        entry_angle_deg=90.0,
        exit_angle_deg=90.0,
    )
    assert_point_close(start, {"lon": 0.0, "lat": 5.0})
    assert_point_close(end, {"lon": 10.0, "lat": 5.0})


def test_side_endpoints_right_basic():
    """
    Simple horizontal segment pointing east.
    Right side should be south (-y).
    """
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:25832",
    )
    start, end = client.compute_side_endpoints_from_vectors(
        entry_lon=0.0,
        entry_lat=0.0,
        exit_lon=10.0,
        exit_lat=0.0,
        entry_tangent_hat=(1.0, 0.0),
        exit_tangent_hat=(1.0, 0.0),
        side="right",
        offset_m=3.0,
        entry_angle_deg=90.0,
        exit_angle_deg=90.0,
    )
    assert_point_close(start, {"lon": 0.0, "lat": -3.0})
    assert_point_close(end, {"lon": 10.0, "lat": -3.0})


def test_entry_and_exit_use_different_vectors():
    """
    Entry and exit vectors must be applied independently.
    """
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:25832",
    )
    entry_tangent_hat = (1.0, 0.0)   
    exit_tangent_hat = (0.0, 1.0)    
    start, end = client.compute_side_endpoints_from_vectors(
        entry_lon=0.0,
        entry_lat=0.0,
        exit_lon=0.0,
        exit_lat=10.0,
        entry_tangent_hat=entry_tangent_hat,
        exit_tangent_hat=exit_tangent_hat,
        side="left",
        offset_m=2.0,
    )
    assert_point_close(start, {"lon": 0.0, "lat": 2.0})
    assert_point_close(end, {"lon": -2.0, "lat": 10.0})


def test_zero_offset_returns_original_points():
    """
    Offset = 0 should return original entry/exit points.
    """
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:25832",
    )

    start, end = client.compute_side_endpoints_from_vectors(
        entry_lon=5.0,
        entry_lat=7.0,
        exit_lon=9.0,
        exit_lat=11.0,
        entry_tangent_hat=(1.0, 0.0),
        exit_tangent_hat=(0.0, 1.0),
        side="left",
        offset_m=0.0,
    )

    assert_point_close(start, {"lon": 5.0, "lat": 7.0})
    assert_point_close(end, {"lon": 9.0, "lat": 11.0})


def test_arbitrary_rotation_angle():
    """
    Non-90-degree rotation should still produce correct offset length.
    """
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:25832",
        output_crs="EPSG:25832",
    )

    start, _ = client.compute_side_endpoints_from_vectors(
        entry_lon=0.0,
        entry_lat=0.0,
        exit_lon=0.0,
        exit_lat=0.0,
        entry_tangent_hat=(1.0, 0.0),
        exit_tangent_hat=(1.0, 0.0),
        side="left",
        offset_m=4.0,
        entry_angle_deg=45.0,
        exit_angle_deg=45.0,
    )

    dist = math.hypot(start["lon"], start["lat"])
    assert abs(dist - 4.0) < 1e-6


if __name__ == "__main__":
    test_side_endpoints_left_basic()
    test_side_endpoints_right_basic()
    test_entry_and_exit_use_different_vectors()
    test_zero_offset_returns_original_points()
    test_arbitrary_rotation_angle()
