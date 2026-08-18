import numpy as np
from typing import List, Dict
from libraries.classes.osrm_api import OSRMClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

LOCATIONS: List[Dict] = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
    {"lon": 12.5900, "lat": 55.6850},
]

def test_osrm_table_local_profiles_distance_and_duration() -> None:
    """
    Integration test for OSRMClient.table covering:
    - profiles: foot, car, bike
    - annotations: distance, duration
    """
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    n = len(LOCATIONS)
    profiles = ["foot", "car", "bike"]
    annotations = ["distance", "duration"]
    for profile in profiles:
        for annotation in annotations:
            print(
                f"\n=== TEST: OSRMClient.table "
                f"(local, profile={profile}, annotation={annotation}) ==="
            )
            client = OSRMClient(base_url="local", profile=profile)
            result = client.table(LOCATIONS, annotations=annotation)
            key = "distances" if annotation == "distance" else "durations"
            assert key in result, f"OSRM response missing '{key}'"
            matrix = np.array(result[key])
            assert matrix.shape == (n, n)
            assert np.allclose(np.diag(matrix), 0.0)
            assert np.all(matrix >= 0)
            if profile == "foot":
                assert np.allclose(matrix, matrix.T, atol=1e-6)
            print(f"{profile.capitalize()} {annotation} matrix:")
            print(matrix)

if __name__ == "__main__":
    test_osrm_table_local_profiles_distance_and_duration()
