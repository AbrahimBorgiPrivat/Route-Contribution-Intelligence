import pytest
from typing import List, Dict
from libraries.utils.preprocessing.osm_segments.osm_snap_points_with_units import (
    snap_points_with_units,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


POINTS: List[Dict[str, float]] = [
    {"lon": 14.7110, "lat": 55.1225},  # Nordskovvej 3
    {"lon": 14.7112, "lat": 55.1221},  # Nordskovvej 4A
    {"lon": 14.7105, "lat": 55.1212},  # Allevej 6
    {"lon": 14.7111, "lat": 55.1220},  # Allevej 18
    {"lon": 14.7107, "lat": 55.1221},  # Allevej 11
    {"lon": 14.7106, "lat": 55.1220},  # Allevej 9
    {"lon": 14.7105, "lat": 55.1218},  # Allevej 7
    {"lon": 14.7090, "lat": 55.1201},  # Jordbærdalen 8
    {"lon": 14.7093, "lat": 55.1200},  # Jordbærdalen 13
]

ADDRESS_NUMBERS: List[int] = [3, 4, 6, 18, 11, 9, 7, 8, 13]


def test_snap_points_with_units_local_basic() -> None:
    """
    Integration test for snap_points_with_units (local OSM service).

    Covers:
    - batch snapping
    - unit grouping
    - unit reuse
    - rotated side-of-road endpoints
    - structural invariants
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM snap service not running",
    )

    print("\n=== TEST: snap_points_with_units (local, rotated side) ===")

    results = snap_points_with_units(
        POINTS,
        address_number=ADDRESS_NUMBERS,
        show_progress=True,
        x_key="lon",
        y_key="lat",
        chunk_size=5,
        use_rotated_side=True,
        offset_m=4.5,
        entry_angle_deg=90.0,
        exit_angle_deg=90.0,
    )

    print("\n--- Results ---")
    for i, r in enumerate(results):
        print(f"\nPoint {i}:")
        print(r)

    assert isinstance(results, list)
    assert len(results) == len(POINTS)

    for r in results:
        assert "segment_id" in r
        assert isinstance(r["segment_id"], int)
        assert r["segment_id"] > 0

        assert "side_of_road" in r
        assert r["side_of_road"] in {"left", "right"}

        assert "unit_number" in r
        assert isinstance(r["unit_number"], int)
        assert r["unit_number"] >= 0

        for key in (
            "unit_start_point_lon",
            "unit_start_point_lat",
            "unit_end_point_lon",
            "unit_end_point_lat",
        ):
            assert key in r
            assert isinstance(r[key], float)


def test_address_number_length_mismatch_raises() -> None:
    """
    address_number length must match points length.
    """
    points = [
        {"x": 1.0, "y": 2.0},
        {"x": 3.0, "y": 4.0},
    ]
    address_numbers = [1]  # wrong length

    with pytest.raises(ValueError, match="address_number must be None or have same length"):
        snap_points_with_units(
            points,
            address_number=address_numbers,
            show_progress=False,
        )


def test_empty_points_returns_empty_list() -> None:
    """
    Empty input should return empty output without error.
    """
    result = snap_points_with_units(
        [],
        address_number=None,
        show_progress=False,
    )

    assert result == []


def test_address_number_even_odd_resolution_without_osm_call(monkeypatch) -> None:
    """
    Verify odd/even logic is applied when side_of_road is None.

    This test bypasses real OSM calls by stubbing client methods.
    """

    class DummyClient:
        def snap_nearest_batch(self, *args, **kwargs):
            return [
                {
                    "segment": {"segment_id": 1},
                    "geometry": {"side_of_road": None},
                },
                {
                    "segment": {"segment_id": 2},
                    "geometry": {"side_of_road": None},
                },
            ]

        def group_segments_on_side(
            self,
            r,
            *,
            allowed_highways=None,
            side_of_road=None,
            use_rotated_side=False,
            offset_m=4.5,
            entry_angle_deg=90.0,
            exit_angle_deg=90.0,
        ):
            return {
                "visited_segments": {r["segment"]["segment_id"]},
                "start_point": {"lon": 0.0, "lat": 0.0},
                "end_point": {"lon": 1.0, "lat": 1.0},
            }

    import libraries.utils.preprocessing.osm_segments.osm_snap_points_with_units as m

    monkeypatch.setattr(m, "OSMSegmentClient", lambda **_: DummyClient())

    points = [{"x": 0, "y": 0}, {"x": 1, "y": 1}]
    address_numbers = [1, 2]  # odd, even

    result = snap_points_with_units(
        points,
        address_number=address_numbers,
        show_progress=False,
    )

    assert result[0]["side_of_road"] == "left"
    assert result[1]["side_of_road"] == "right"


def test_snap_points_with_units_rotated_vs_raw() -> None:
    """
    Integration sanity test:
    rotated side endpoints should differ from raw endpoints.
    """
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM snap service not running",
    )

    print("\n=== TEST: snap_points_with_units (rotated vs raw) ===")

    raw = snap_points_with_units(
        POINTS[:2],
        address_number=ADDRESS_NUMBERS[:2],
        show_progress=False,
        x_key="lon",
        y_key="lat",
        use_rotated_side=False,
    )

    rotated = snap_points_with_units(
        POINTS[:2],
        address_number=ADDRESS_NUMBERS[:2],
        show_progress=False,
        x_key="lon",
        y_key="lat",
        use_rotated_side=True,
        offset_m=4.5,
        entry_angle_deg=90.0,
        exit_angle_deg=90.0,
    )

    for r_raw, r_rot in zip(raw, rotated):
        assert (
            r_raw["unit_start_point_lon"] != r_rot["unit_start_point_lon"]
            or r_raw["unit_start_point_lat"] != r_rot["unit_start_point_lat"]
            or r_raw["unit_end_point_lon"] != r_rot["unit_end_point_lon"]
            or r_raw["unit_end_point_lat"] != r_rot["unit_end_point_lat"]
        )


if __name__ == "__main__":
    test_snap_points_with_units_local_basic()
    test_empty_points_returns_empty_list()
    test_address_number_length_mismatch_raises()
    test_snap_points_with_units_rotated_vs_raw()
