import pytest
from libraries.classes.osrm_api import OSRMClient


# --------------------------------------------------
# Example route (INDEX-BASED, R == index)
# --------------------------------------------------
LOCATIONS = [
    {
        "lon": 14.711,
        "lat": 55.1225,
        "unit_number": 0,
        "unit_start_point_lon": 14.711079,
        "unit_start_point_lat": 55.122285,
        "unit_end_point_lon": 14.709811,
        "unit_end_point_lat": 55.122587,
    },
    {
        "lon": 14.7107,
        "lat": 55.1225,
        "unit_number": 1,
        "unit_start_point_lon": 14.709811,
        "unit_start_point_lat": 55.122587,
        "unit_end_point_lon": 14.711079,
        "unit_end_point_lat": 55.122285,
    },
    {
        "lon": 14.7104,
        "lat": 55.1223,
        "unit_number": 1,
        "unit_start_point_lon": 14.709811,
        "unit_start_point_lat": 55.122587,
        "unit_end_point_lon": 14.711079,
        "unit_end_point_lat": 55.122285,
    },
    {
        "lon": 14.7111,
        "lat": 55.1225,
        "unit_number": 0,
        "unit_start_point_lon": 14.711079,
        "unit_start_point_lat": 55.122285,
        "unit_end_point_lon": 14.709811,
        "unit_end_point_lat": 55.122587,
    },
]

R = [0, 1, 2, 3]


# --------------------------------------------------
# Core behavior test
# --------------------------------------------------
def test_build_locations_for_route_index_based_all_problem_types():
    client = OSRMClient()

    cases = {
        "TSP": [
            {"lon": 14.711, "lat": 55.1225},
            {"lon": 14.7107, "lat": 55.1225},
            {"lon": 14.7104, "lat": 55.1223},
            {"lon": 14.7111, "lat": 55.1225},
            {"lon": 14.711, "lat": 55.1225},
        ],
        "HPP": [
            {"lon": 14.711, "lat": 55.1225},
            {"lon": 14.7107, "lat": 55.1225},
            {"lon": 14.7104, "lat": 55.1223},
            {"lon": 14.7111, "lat": 55.1225},
        ],
        "OUT:HPP": [
            {'lon': 14.711, 'lat': 55.1225},
            {'lon': 14.709811, 'lat': 55.122587},
            {'lon': 14.7107, 'lat': 55.1225},
            {'lon': 14.7104, 'lat': 55.1223},
            {'lon': 14.711079, 'lat': 55.122285},
            {'lon': 14.7111, 'lat': 55.1225}
        ],
        "OUT:TSP": [
            {'lon': 14.711, 'lat': 55.1225},
            {'lon': 14.709811, 'lat': 55.122587},
            {'lon': 14.7107, 'lat': 55.1225},
            {'lon': 14.7104, 'lat': 55.1223},
            {'lon': 14.711079, 'lat': 55.122285},
            {'lon': 14.7111, 'lat': 55.1225},
            {'lon': 14.711, 'lat': 55.1225}
        ],
    }

    for problem_type, expected in cases.items():
        path = client._build_locations_for_route(
            locations=LOCATIONS,
            R=R,
            problem_type=problem_type,
        )
        print(f"\n=== {problem_type} ===")
        for p in path:
            print(p)
        assert path == expected


# --------------------------------------------------
# Failure cases
# --------------------------------------------------
def test_missing_required_keys_structured_raises_1():
    client = OSRMClient()
    bad_locations = [
        {
            "lon": 14.7110,
            "unit_number": 0,
        }
    ]
    with pytest.raises(KeyError):
        client._build_locations_for_route(
            locations=bad_locations,
            R=[0],
            problem_type="HPP",
        )


def test_missing_required_keys_structured_raises_2():
    client = OSRMClient()
    bad_locations = [
        {
            "lon": 14.7110,
            "lat": 55.1225,
            "unit_number": 0,
        }
    ]
    with pytest.raises(KeyError):
        client._build_locations_for_route(
            locations=bad_locations,
            R=[0],
            problem_type="OUT:HPP",
        )

def test_invalid_problem_type_raises():
    client = OSRMClient()

    with pytest.raises(ValueError):
        client._build_locations_for_route(
            locations=LOCATIONS,
            R=R,
            problem_type="INVALID",
        )

def test_length_mismatch_raises():
    client = OSRMClient()
    with pytest.raises(ValueError):
        client._build_locations_for_route(
            locations=LOCATIONS,
            R=[0, 1, 2, 3, 4, 5],  
            problem_type="TSP",
        )

if __name__ == "__main__":
    test_build_locations_for_route_index_based_all_problem_types()
    test_missing_required_keys_structured_raises_1()
    test_missing_required_keys_structured_raises_2()
    test_invalid_problem_type_raises()
    test_length_mismatch_raises()
