import numpy as np
from typing import List, Dict
from libraries.classes.osrm_api import OSRMClient
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

LOCATIONS: List[Dict] = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
    {"lon": 12.5900, "lat": 55.6850},
]


def test_osrm_table_chunked_local_profiles_distance_and_duration() -> None:
    """
    Integration test for OSRMClient.table_chunked covering:
    - profiles: foot, car, bike
    - annotations: distance, duration
    - consistency with non-chunked table
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
                f"\n=== TEST: OSRMClient.table_chunked "
                f"(local, profile={profile}, annotation={annotation}) ==="
            )
            client = OSRMClient(base_url="local", profile=profile)
            # --- Chunked ---
            M_chunked = client.table_chunked(
                LOCATIONS,
                chunk_size=2,              
                annotations=annotation,
                profile=profile,
            )
            assert M_chunked.shape == (n, n)
            assert np.allclose(np.diag(M_chunked), 0.0)
            assert np.all(M_chunked >= 0)
            # --- Non-chunked (reference) ---
            result = client.table(LOCATIONS, annotations=annotation)
            key = "distances" if annotation == "distance" else "durations"
            M_full = np.array(result[key])

            # --- Consistency check ---
            assert np.allclose(
                M_chunked,
                M_full,
                atol=1e-6,
            ), "Chunked and non-chunked results differ"
            # Foot routing is usually symmetric
            if profile == "foot":
                assert np.allclose(M_chunked, M_chunked.T, atol=1e-6)
            print(f"{profile.capitalize()} {annotation} matrix (chunked):")
            print(M_chunked)


if __name__ == "__main__":
    test_osrm_table_chunked_local_profiles_distance_and_duration()
