import pandas as pd
import numpy as np

from libraries.utils.preprocessing.osrm.osrm_data import prepare_route_data
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

STRUCTURED_PROBLEM_TYPE = "OUT:TSP"
UNSTRUCTURED_PROBLEM_TYPE = "TSP"


def test_prepare_route_data_full_structured_and_unstructured() -> None:
    # --------------------------------------------------
    # Required skip (OSRM)
    # --------------------------------------------------
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )

    print("\n=== TEST: prepare_route_data (FULL) ===")

    # ==================================================
    # PART 1: STRUCTURED ROUTE
    # ==================================================
    print("\n--- Structured route case ---")

    structured_data = {
        "route_nr": [0, 1, 2, 3, 4, 5, 6],
        "lon": [
            12.5683, 12.5690, 12.5692,   
            12.5710, 12.5720,   
            12.5740, 12.5750,   
        ],
        "lat": [
            55.6761, 55.6768, 55.6763,
            55.6778, 55.6784,
            55.6795, 55.6802,
        ],
        "n_postboxes": [1, 2, 3, 1, 1, 2, 1],
        "unit_number": [0, 0, 0, 1, 1, 2, 2],
        "unit_start_point_lon": [
            12.5660, 12.5660, 12.5660,
            12.5700, 12.5700,
            12.5730, 12.5730,
        ],
        "unit_start_point_lat": [
            55.6750, 55.6750, 55.6750,
            55.6770, 55.6770,
            55.6790, 55.6790,
        ],
        "unit_end_point_lon": [
            12.5705, 12.5705, 12.5705,
            12.5735, 12.5735,
            12.5760, 12.5760,
        ],
        "unit_end_point_lat": [
            55.6775, 55.6775, 55.6775,
            55.6790, 55.6790,
            55.6810, 55.6810,
        ],
    }

    df_structured = pd.DataFrame(structured_data)

    print("\nStructured input dataframe:")
    print(df_structured)

    structured_result = prepare_route_data(
        data=df_structured,
        problem_type=STRUCTURED_PROBLEM_TYPE,
        chunk_size=10,
        profile="foot",
        annotation="distance",
    )

    D_s = structured_result["Distance_Matrix"]
    p_s = structured_result["p"]
    R_s = structured_result["R"]
    nodes_s = structured_result["nodes"]

    print("\nStructured Distance_Matrix shape:", D_s.shape)
    print("Structured p:", p_s)
    print("Structured R:", R_s)
    print("\nStructured nodes:")
    for n in nodes_s:
        print(n)

    # -----------------------------
    # Assertions: structured
    # -----------------------------
    assert isinstance(D_s, np.ndarray)
    assert D_s.ndim == 2
    assert D_s.shape[0] == D_s.shape[1]

    # Structured expands locations (start + addresses + end)
    assert D_s.shape[0] > len(df_structured)

    assert isinstance(p_s, np.ndarray)
    assert list(p_s) == [1, 2, 3, 1, 1, 2, 1]

    assert R_s == [0, 1, 2, 3, 4, 5, 6]

    assert nodes_s is not None
    assert isinstance(nodes_s, list)
    assert len(nodes_s) == D_s.shape[0]

    for i, node in enumerate(nodes_s):
        assert node["m_index"] == i
        assert node["type"] in {"start", "address", "end"}
        assert isinstance(node["unit"], int)
        if node["type"] == "address":
            assert isinstance(node["route_number"], int)
        else:
            assert node["route_number"] is None

    # ==================================================
    # PART 2: UNSTRUCTURED ROUTE
    # ==================================================
    print("\n--- Unstructured route case ---")

    unstructured_data = {
        "route_nr": [0, 1, 2],
        "lon": [12.5683, 12.5700, 12.5720],
        "lat": [55.6761, 55.6770, 55.6780],
        "n_postboxes": [1, 2, 1],
    }

    df_unstructured = pd.DataFrame(unstructured_data)

    print("\nUnstructured input dataframe:")
    print(df_unstructured)

    unstructured_result = prepare_route_data(
        data=df_unstructured,
        problem_type=UNSTRUCTURED_PROBLEM_TYPE,
        chunk_size=10,
        profile="foot",
        annotation="distance",
    )

    D_u = unstructured_result["Distance_Matrix"]
    p_u = unstructured_result["p"]
    R_u = unstructured_result["R"]
    nodes_u = unstructured_result["nodes"]

    print("\nUnstructured Distance_Matrix shape:", D_u.shape)
    print("Unstructured p:", p_u)
    print("Unstructured R:", R_u)
    print("Unstructured nodes:", nodes_u)

    # -----------------------------
    # Assertions: unstructured
    # -----------------------------
    assert isinstance(D_u, np.ndarray)
    assert D_u.ndim == 2
    assert D_u.shape == (len(df_unstructured), len(df_unstructured))

    assert isinstance(p_u, np.ndarray)
    assert list(p_u) == [1, 2, 1]

    assert R_u == [0, 1, 2]

    assert nodes_u is None

    print("\n=== FULL prepare_route_data test PASSED ===")


if __name__ == "__main__":
    test_prepare_route_data_full_structured_and_unstructured()
