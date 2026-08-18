from typing import List, Dict
from libraries.classes.osrm_api import OSRMClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

LOCATIONS: List[Dict] = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
]

def test_osrm_route_local_with_variants() -> None:
    """
    Integration test for OSRMClient.route with different parameter combinations.
    Tests correctness of request wiring and response structure.
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    client = OSRMClient(base_url="local", profile="foot")
    test_cases = [
        {
            "name": "default_route",
            "kwargs": {},
        },
        {
            "name": "with_steps",
            "kwargs": {
                "steps": True,
            },
        },
        {
            "name": "full_overview_geojson",
            "kwargs": {
                "overview": "full",
                "geometries": "geojson",
            },
        },
        {
            "name": "with_annotations",
            "kwargs": {
                "annotations": "distance",
            },
        },
        {
            "name": "alternatives_enabled",
            "kwargs": {
                "alternatives": True,
            },
        },
    ]
    for case in test_cases:
        print(f"\n=== TEST: OSRMClient.route – {case['name']} ===")
        result = client.route(
            LOCATIONS,
            **case["kwargs"],
        )
        # ---- Structural assertions ----
        assert "routes" in result
        assert isinstance(result["routes"], list)
        assert len(result["routes"]) >= 1
        route0 = result["routes"][0]
        # Duration and distance always present
        assert "distance" in route0
        assert "duration" in route0
        assert route0["distance"] >= 0
        assert route0["duration"] >= 0
        # Geometry presence depends on overview
        if case["kwargs"].get("overview") != "false":
            assert "geometry" in route0
        # Steps only present if requested
        if case["kwargs"].get("steps"):
            assert "legs" in route0
            assert "steps" in route0["legs"][0]
        print("Distance:", route0["distance"])
        print("Duration:", route0["duration"])

if __name__ == "__main__":
    test_osrm_route_local_with_variants()