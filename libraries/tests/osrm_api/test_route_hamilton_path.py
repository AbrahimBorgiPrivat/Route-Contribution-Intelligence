from typing import List, Dict
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable
from libraries.classes.osrm_api import OSRMClient
import pytest

LOCATIONS: List[Dict] = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
    {"lon": 12.5900, "lat": 55.6850},
]

STRUCTURED_LOCATIONS = [
    {
        "lon": 12.5683,
        "lat": 55.6761,
        "unit_number": 0,
        "unit_start_point_lon": 12.5660,
        "unit_start_point_lat": 55.6750,
        "unit_end_point_lon": 12.5705,
        "unit_end_point_lat": 55.6775,
    },
    {
        "lon": 12.5700,
        "lat": 55.6770,
        "unit_number": 0,
        "unit_start_point_lon": 12.5660,
        "unit_start_point_lat": 55.6750,
        "unit_end_point_lon": 12.5705,
        "unit_end_point_lat": 55.6775,
    },
    {
        "lon": 12.5720,
        "lat": 55.6780,
        "unit_number": 1,
        "unit_start_point_lon": 12.5715,
        "unit_start_point_lat": 55.6775,
        "unit_end_point_lon": 12.5740,
        "unit_end_point_lat": 55.6790,
    },
]

def _assert_steps_valid(steps_list: list, expected_legs: int):
    assert isinstance(steps_list, list)
    assert len(steps_list) == expected_legs
    for leg_steps in steps_list:
        assert isinstance(leg_steps, list)
        assert len(leg_steps) > 0
        step0 = leg_steps[0]
        assert "distance" in step0
        assert "duration" in step0
        assert step0["distance"] >= 0
        assert step0["duration"] >= 0

def test_osrm_route_hamilton_path_local_profiles_TSP_and_HPP() -> None:
    """
    Integration test for OSRMClient.route_hamilton_path covering:
    - profiles: foot, car, bike
    - problem_type: TSP (cycle) and HPP (path)
    - default R
    - explicit R
    - structural correctness of returned steps
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    profiles = ["foot", "car", "bike"]
    n = len(LOCATIONS)
    for profile in profiles:
        print(f"\n=== TEST: route_hamilton_path (profile={profile}) ===")
        client = OSRMClient(base_url="local", profile=profile)
        # -------------------------
        # Case 1: Default R — TSP
        # -------------------------
        steps_tsp = client.route_hamilton_path(
            LOCATIONS,
            problem_type="TSP",
        )
        _assert_steps_valid(steps_tsp, expected_legs=n)
        print(f"TSP default R produced {len(steps_tsp)} legs")
        # -------------------------
        # Case 2: Default R — HPP
        # -------------------------
        steps_hpp = client.route_hamilton_path(
            LOCATIONS,
            problem_type="HPP",
        )
        _assert_steps_valid(steps_hpp, expected_legs=n - 1)
        print(f"HPP default R produced {len(steps_hpp)} legs")
        # -------------------------
        # Case 3: Explicit R — TSP
        # -------------------------
        R = list(reversed(range(n)))
        steps_tsp_R = client.route_hamilton_path(
            LOCATIONS,
            R=R,
            problem_type="TSP",
        )
        _assert_steps_valid(steps_tsp_R, expected_legs=n)
        print(f"TSP explicit R produced {len(steps_tsp_R)} legs")
        # -------------------------
        # Case 4: Explicit R — HPP
        # -------------------------
        steps_hpp_R = client.route_hamilton_path(
            LOCATIONS,
            R=R,
            problem_type="HPP",
        )
        _assert_steps_valid(steps_hpp_R, expected_legs=n - 1)
        print(f"HPP explicit R produced {len(steps_hpp_R)} legs")

def test_route_hamilton_path_returns_empty_for_single_location() -> None:
    """
    If fewer than 2 locations are provided, return empty list.
    Applies to both TSP and HPP.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    steps_tsp = client.route_hamilton_path(
        [LOCATIONS[0]],
        problem_type="TSP",
    )
    steps_hpp = client.route_hamilton_path(
        [LOCATIONS[0]],
        problem_type="HPP",
    )
    assert steps_tsp == []
    assert steps_hpp == []

def test_route_hamilton_path_invalid_R_index_out_of_bounds() -> None:
    """
    If R contains an index >= len(locations), raise ValueError.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    R = [0, 1, 99]
    with pytest.raises(ValueError):
        client.route_hamilton_path(LOCATIONS, R=R)

def test_route_hamilton_path_invalid_R_negative_index() -> None:
    """
    If R contains a negative index, raise ValueError.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    R = [0, -1, 1]
    with pytest.raises(ValueError):
        client.route_hamilton_path(LOCATIONS, R=R)

def test_route_hamilton_path_invalid_R_non_integer() -> None:
    """
    If R contains a non-integer, raise TypeError.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    R = [0, "1", 2]
    with pytest.raises(TypeError):
        client.route_hamilton_path(LOCATIONS, R=R)


def test_route_hamilton_path_R_too_short() -> None:
    """
    If R has fewer than 2 elements, return empty list.
    Applies to both TSP and HPP.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    steps_tsp = client.route_hamilton_path(
        LOCATIONS,
        R=[0],
        problem_type="TSP",
    )
    steps_hpp = client.route_hamilton_path(
        LOCATIONS,
        R=[0],
        problem_type="HPP",
    )
    assert steps_tsp == []
    assert steps_hpp == []

def test_route_hamilton_path_out_hpp() -> None:
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    R = [0, 1, 2]
    steps = client.route_hamilton_path(
        STRUCTURED_LOCATIONS,
        R=R,
        problem_type="OUT:HPP",
    )
    print("\nOUT:HPP produced steps:")
    for i, leg in enumerate(steps):
        print(f"  leg {i}: {len(leg)} steps")
    assert isinstance(steps, list)
    assert len(steps) == 4
    for leg in steps:
        assert isinstance(leg, list)
        assert len(leg) > 0

def test_route_hamilton_path_out_tsp() -> None:
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    R = [0, 1, 2]
    steps = client.route_hamilton_path(
        STRUCTURED_LOCATIONS,
        R=R,
        problem_type="OUT:TSP",
    )
    for i, leg in enumerate(steps):
        print(f"  leg {i}: {len(leg)} steps")
    assert isinstance(steps, list)
    assert len(steps) == 7
    for leg in steps:
        assert isinstance(leg, list)
        assert len(leg) > 0

if __name__ == "__main__":
    test_osrm_route_hamilton_path_local_profiles_TSP_and_HPP()
    test_route_hamilton_path_returns_empty_for_single_location()
    test_route_hamilton_path_invalid_R_index_out_of_bounds()
    test_route_hamilton_path_invalid_R_negative_index()
    test_route_hamilton_path_invalid_R_non_integer()
    test_route_hamilton_path_R_too_short()
    test_route_hamilton_path_out_hpp()
    test_route_hamilton_path_out_tsp()