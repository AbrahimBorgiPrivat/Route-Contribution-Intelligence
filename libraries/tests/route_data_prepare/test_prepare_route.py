import os
import pandas as pd
from libraries.utils.preprocessing.route_data_preparer import prepare_route, prepare_dataset_for_runner
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable

# ---------------------------------------------------------------------
# Shared APR configuration used by all tests
# ---------------------------------------------------------------------
APR = {
    "foot": {
        "distance": 1.0,
        "duration": 0.02,
    },
    "car": {
        "distance": 0.5,
        "duration": 0.01,
    },
}


def test_case_1_basic_route_deduplication_and_resolution() -> None:
    """
    Basic test:
    - duplicate (lon, lat) with increasing line_nr
    - deduplication keeps first occurrence by line_nr
    - route_nr is reassigned 0..n-1
    - APR profile and problem_type are resolved
    """
    data = {
        "route_id": [1, 1, 1, 1],
        "lon": [14.71, 14.71, 14.72, 14.80],
        "lat": [55.12, 55.12, 55.13, 55.20],
        "line_nr": [0, 1, 2, 3],
        "distance_type": ["foot", "foot", "foot", "foot"],
        "annotation_type": ["distance", "distance", "distance", "distance"],
        "problem_type": ["TSP", "TSP", "TSP", "TSP"],
    }
    df = pd.DataFrame(data)
    result = prepare_route(route_id=1, df=df, APR=APR)
    route_df = result["data"]
    apr_profile = result["APR_profile"]
    problem_type = result["problem_type"]
    # -----------------------------
    # Route data assertions
    # -----------------------------
    assert len(route_df) == 3
    assert list(route_df["line_nr"]) == [0, 2, 3]
    assert list(route_df["route_nr"]) == [0, 1, 2]
    # -----------------------------
    # APR profile resolution
    # -----------------------------
    assert apr_profile["profile"] == "foot"
    assert apr_profile["annotation"] == "distance"
    assert apr_profile["APR"] == APR["foot"]["distance"]
    assert apr_profile["unit"] == "m"
    # -----------------------------
    # Problem type resolution
    # -----------------------------
    assert problem_type == "TSP"

def test_case_2_multiple_routes_independent_resolution() -> None:
    """
    Multiple route_ids:
    - each route is resolved independently
    - route_nr always starts at 0 per route
    - problem_type can differ per route
    """
    data = {
        "route_id": [1, 1, 2, 2],
        "lon": [14.71, 14.72, 14.80, 14.81],
        "lat": [55.12, 55.13, 55.20, 55.21],
        "line_nr": [0, 1, 0, 1],
        "distance_type": ["foot", "foot", "car", "car"],
        "annotation_type": ["distance", "distance", "duration", "duration"],
        "problem_type": ["TSP", "TSP", "HPP", "HPP"],
    }
    df = pd.DataFrame(data)
    result_r1 = prepare_route(route_id=1, df=df, APR=APR)
    result_r2 = prepare_route(route_id=2, df=df, APR=APR)

    # -----------------------------
    # Route 1
    # -----------------------------
    r1_df = result_r1["data"]
    assert len(r1_df) == 2
    assert list(r1_df["route_nr"]) == [0, 1]
    assert result_r1["problem_type"] == "TSP"
    assert result_r1["APR_profile"]["profile"] == "foot"
    assert result_r1["APR_profile"]["unit"] == "m"

    # -----------------------------
    # Route 2
    # -----------------------------
    r2_df = result_r2["data"]
    assert len(r2_df) == 2
    assert list(r2_df["route_nr"]) == [0, 1]
    assert result_r2["problem_type"] == "HPP"
    assert result_r2["APR_profile"]["profile"] == "car"
    assert result_r2["APR_profile"]["unit"] == "sec"

def test_case_3_structured_route_adds_unit_columns() -> None:
    """
    Structured route test:
    - problem_type is structured (OUT:TSP)
    - prepare_route must call snap_points_with_units
    - structural columns are added to the route dataframe
    """

    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM Snap service not running",
    )

    data = {
        "route_id": [10, 10, 10, 10],
        "lon": [14.7110, 14.7107, 14.7104, 14.7111],
        "lat": [55.1225, 55.1225, 55.1223, 55.1225],
        "line_nr": [0, 1, 2,3],
        "distance_type": ["foot", "foot", "foot", "foot"],
        "annotation_type": ["distance", "distance", "distance", "distance"],
        "problem_type": ["OUT:TSP", "OUT:TSP", "OUT:TSP", "OUT:TSP"],
    }

    df = pd.DataFrame(data)

    result = prepare_route(
        route_id=10,
        df=df,
        APR=APR,
    )

    route_df = result["data"]
    print(route_df.head())
    assert len(route_df) == 4
    assert list(route_df["route_nr"]) == [0, 1, 2, 3]
    assert result["problem_type"] == "OUT:TSP"
    for col in [
        "segment_id",
        "side_of_road",
        "unit_number",
        "unit_start_point_lon",
        "unit_start_point_lat",
        "unit_end_point_lon",
        "unit_end_point_lat",
    ]:
        assert col in route_df.columns
    assert route_df["segment_id"].notnull().all()
    assert (route_df["segment_id"] > 0).all()
    assert route_df["side_of_road"].isin({"left", "right"}).all()
    assert route_df["unit_number"].dtype.kind in {"i", "u"}
    assert (route_df["unit_number"] >= 0).all()

def test_case_4_prepare_route_preserves_revenue_column():
    """
    Integration test:
    - prepare_dataset_for_runner attaches revenue
    - prepare_route is called on that dataframe
    - route-level data still contains the 'revenue' column
    """
    print("\n=== TEST: prepare_route preserves revenue column ===")
    csv_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_data.csv"
    )
    csv_rev_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_revenue_data.csv"
    )
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "revenue": {
            "path_revenue": csv_rev_path,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": [
                "week_2536",
                "week_2537",
                "week_2538",
                "week_2539",
            ],
            "rev_formula": "AVG",
            "rev_include_all_addresses": True,
        },
    }
    # --------------------------------------------------
    # Step 1: prepare dataset (attach revenue here)
    # --------------------------------------------------
    df = prepare_dataset_for_runner(
        file_path=csv_path,
        col_map=col_map,
    )
    assert "revenue" in df.columns
    print("[INFO] Revenue column present after dataset preparation")
    # --------------------------------------------------
    # Step 2: prepare route
    # --------------------------------------------------
    route_id = df["route_id"].iloc[0]
    result = prepare_route(
        route_id=route_id,
        df=df,
        APR=APR,
    )
    route_df = result["data"]
    print(route_df.head())
    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------
    assert "revenue" in route_df.columns
    assert route_df["revenue"].dtype.kind in {"f", "i"}
    assert (route_df["revenue"] >= 0.0).all()
    print("[OK] Revenue column preserved through prepare_route")

def test_case_5_prepare_route_unit_entry_exit_strategies() -> None:
    """
    Structured route test with explicit unit_entry_exit_strategy:
    - SNAPPED (default / None): uses snapped unit start/end
    - FIRST_LAST_ADDRESS: entry = first address, exit = last address
    - OSRM_CLOSEST: entry/exit chosen via OSRM distance
    """
    print("\n=== TEST: prepare_route unit_entry_exit_strategy ===")
    # --------------------------------------------------
    # Required services
    # --------------------------------------------------
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM Snap service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    data = {
        "route_id": [99, 99, 99],
        "lon": [12.5683, 12.5690, 12.5700],
        "lat": [55.6761, 55.6768, 55.6772],
        "line_nr": [0, 1, 2],
        "distance_type": ["foot", "foot", "foot"],
        "annotation_type": ["distance", "distance", "distance"],
        "problem_type": ["OUT:TSP", "OUT:TSP", "OUT:TSP"],
    }
    df = pd.DataFrame(data)

    # ==================================================
    # Strategy 1: SNAPPED (default)
    # ==================================================
    result_snapped = prepare_route(
        route_id=99,
        df=df,
        APR=APR,
        unit_entry_exit_strategy=None,  
    )
    snapped_df = result_snapped["data"]
    print("\n--- SNAPPED ---")
    print(snapped_df)
    snapped_start = snapped_df.loc[0, "unit_start_point_lon"]
    snapped_end = snapped_df.loc[0, "unit_end_point_lon"]

    # ==================================================
    # Strategy 2: FIRST_LAST_ADDRESS
    # ==================================================
    result_first_last = prepare_route(
        route_id=99,
        df=df,
        APR=APR,
        unit_entry_exit_strategy="FIRST_LAST_ADDRESS",
    )
    fl_df = result_first_last["data"]
    print("\n--- FIRST_LAST_ADDRESS ---")
    print(fl_df)
    for unit_id, g in fl_df.groupby("unit_number"):
        g = g.sort_values("route_nr")
        first_lon = g.iloc[0]["lon"]
        last_lon = g.iloc[-1]["lon"]
        assert (g["unit_start_point_lon"] == first_lon).all()
        assert (g["unit_end_point_lon"] == last_lon).all()
    # ==================================================
    # Strategy 3: OSRM_CLOSEST
    # ==================================================
    result_osrm = prepare_route(
        route_id=99,
        df=df,
        APR=APR,
        unit_entry_exit_strategy="OSRM_CLOSEST",
    )
    osrm_df = result_osrm["data"]
    print("\n--- OSRM_CLOSEST ---")
    print(osrm_df)
    assert osrm_df.loc[0, "unit_start_point_lon"] in df["lon"].values
    assert osrm_df.loc[0, "unit_end_point_lon"] in df["lon"].values
    assert (
        osrm_df.loc[0, "unit_start_point_lon"] != snapped_start
        or osrm_df.loc[0, "unit_end_point_lon"] != snapped_end
    )

if __name__ == "__main__":
    test_case_1_basic_route_deduplication_and_resolution()
    test_case_2_multiple_routes_independent_resolution()
    test_case_3_structured_route_adds_unit_columns()
    test_case_4_prepare_route_preserves_revenue_column()
    test_case_5_prepare_route_unit_entry_exit_strategies()