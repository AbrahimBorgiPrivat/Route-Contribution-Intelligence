import os
import tempfile
import pytest
from typing import Dict
import pandas as pd
from libraries.utils.preprocessing.route_data_preparer import prepare_dataset_for_runner

def _write_temp_csv(df: pd.DataFrame) -> str:
    """Helper: write DataFrame to a temp CSV and return its path."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="test_prepare_ds_")
    os.close(tmp_fd)  
    df.to_csv(tmp_path, sep=";", index=False)
    return tmp_path

def test_case_1_basic_no_transform() -> None:
    """
    Basic test:
    - simple CSV with id, vejx, vejy, linienr, beregning
    - mapping without EPSG transform
    - lon/lat numeric
    - n_postboxes correct
    - default distance_type / annotation_type applied
    """
    print("\n=== TEST CASE 1: Basic dataset preparation (no EPSG transform) ===")
    data = {
        "id": [1, 1, 1, 2],
        "vejx": ["14,71", "14,71", "14,72", "14,80"],
        "vejy": ["55,12", "55,12", "55,13", "55,20"],
        "linienr": [0, 1, 2, 0],
        "beregning": [0, 0, 0, 1],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
    }
    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    for col in ["route_id", "lon", "lat", "line_nr", "n_postboxes",
                "distance_type", "annotation_type"]:
        assert col in df_clean.columns
    assert set(df_clean["distance_type"]) == {"foot"}
    assert set(df_clean["annotation_type"]) == {"distance"}
    counts = df_clean["n_postboxes"].tolist()
    assert counts[0] == 2
    assert counts[1] == 2
    assert counts[2] == 1

    os.remove(csv_path)


def test_case_2_with_transform_identity() -> None:
    """
    Test with EPSG transform:
    - Use EPSG:4326 -> EPSG:4326 (identity) to exercise transform code path
    - lon/lat values should remain close to original floats
    """
    print("\n=== TEST CASE 2: Dataset preparation with EPSG transform (identity) ===")

    data = {
        "id": [10, 10],
        "vejx": ["14,71", "14,72"],
        "vejy": ["55,12", "55,13"],
        "linienr": [0, 1],
        "beregning": [0, 0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map: Dict[str, Dict[str, str]] = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "transform": {
            "convert_from": "EPSG:4326",
            "convert_to": "EPSG:4326",
        },
    }
    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    print("\n[RESULT] Cleaned dataset with transform:")
    print(df_clean)
    assert "lon" in df_clean.columns and "lat" in df_clean.columns
    assert df_clean["route_id"].iloc[0] == 10
    lon_vals = df_clean["lon"].tolist()
    lat_vals = df_clean["lat"].tolist()
    print("lon:", lon_vals)
    print("lat:", lat_vals)
    assert abs(lon_vals[0] - 14.71) < 1e-6
    assert abs(lat_vals[0] - 55.12) < 1e-6

    os.remove(csv_path)

def test_case_3_existing_internal_columns_conflict() -> None:
    """
    Test conflict handling:
    - CSV already has 'lon' and 'lat' columns, plus 'vejx'/'vejy'
    - We map vejx->lon, vejy->lat
    - Original lon/lat must be renamed to lon_orig / lat_orig
    """
    print("\n=== TEST CASE 3: Existing lon/lat conflict resolution ===")

    data = {
        "id": [1, 1],
        "vejx": ["14,71", "14,72"],
        "vejy": ["55,12", "55,13"],
        "lon": [100.0, 200.0],  # old lon column
        "lat": [300.0, 400.0],  # old lat column
        "linienr": [0, 1],
        "beregning": [0, 0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map: Dict[str, Dict[str, str]] = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},   
        "lat": {"name": "vejy"},   
        "line_nr": {"name": "linienr"},
    }
    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    print("\n[RESULT] Cleaned dataset with conflict resolution:")
    print(df_clean)
    assert "lon_orig" in df_clean.columns
    assert "lat_orig" in df_clean.columns
    assert "lon" in df_clean.columns
    assert "lat" in df_clean.columns
    assert df_clean["route_id"].iloc[0] == 1
    assert list(df_clean["line_nr"]) == [0, 1]

    os.remove(csv_path)


def test_case_4_missing_mapped_column_raises() -> None:
    """
    If col_map refers to a source column that does not exist, raise KeyError.
    """
    print("\n=== TEST CASE 4: Missing mapped column raises KeyError ===")

    data = {
        "id": [1],
        "vejx": ["14,71"],
        # "vejy" is missing on purpose
        "linienr": [0],
        "beregning": [0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)

    col_map: Dict[str, Dict[str, str]] = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"}, 
        "line_nr": {"name": "linienr"},
    }

    error_raised = False
    try:
        _ = prepare_dataset_for_runner(csv_path, col_map)
    except KeyError as e:
        print("KeyError correctly raised:", e)
        error_raised = True

    assert error_raised is True

    os.remove(csv_path)

def test_case_5_type_mapping_to_distance_and_annotation() -> None:
    """
    Test that col_map["type"] correctly derives:
    - distance_type
    - annotation_type
    from a coded column (beregning).
    """
    print("\n=== TEST CASE 5: Type mapping ===")

    data = {
        "id": [1, 1, 1],
        "vejx": ["14,71", "14,72", "14,73"],
        "vejy": ["55,12", "55,13", "55,14"],
        "linienr": [0, 1, 2],
        "beregning": [0, 1, 2],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)

    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "type": {
            "name": "beregning",
            "foot": {"val": 0, "annotations": "distance"},
            "cycle": {"val": 1, "annotations": "distance"},
            "car": {"val": 2, "annotations": "duration"},
        },
    }

    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    print("\n[RESULT] Cleaned dataset with conflict resolution:")
    print(df_clean)
    assert list(df_clean["distance_type"]) == ["foot", "cycle", "car"]
    assert list(df_clean["annotation_type"]) == ["distance", "distance", "duration"]

    os.remove(csv_path)


def test_case_5b_preserve_optional_L_u_column() -> None:
    """
    Optional L_u mapping is preserved and coerced to numeric.
    """
    data = {
        "id": [1, 1],
        "vejx": ["14,71", "14,72"],
        "vejy": ["55,12", "55,13"],
        "linienr": [0, 1],
        "dwell_seconds": ["30", "30"],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)

    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "L_u": {"name": "dwell_seconds"},
    }

    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    assert "L_u" in df_clean.columns
    assert df_clean["L_u"].tolist() == [30.0, 30.0]

    os.remove(csv_path)

def test_case_5c_selector_filters_rows() -> None:
    """
    Optional selector should filter rows before the rest of the preparation.
    """
    data = {
        "id": ["A", "A", "B"],
        "route_group": ["Day Busses", "Night", "Day Busses"],
        "vejx": ["14,71", "14,72", "14,73"],
        "vejy": ["55,12", "55,13", "55,14"],
        "linienr": [0, 1, 2],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)

    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
    }

    df_clean = prepare_dataset_for_runner(
        csv_path,
        col_map,
        selector={
            "column": "route_group",
            "values": ["Day Busses"],
        },
    )

    assert list(df_clean["route_id"].unique()) == ["A", "B"]
    assert len(df_clean) == 2
    assert set(df_clean["route_group"]) == {"Day Busses"}

    os.remove(csv_path)

def test_case_6_missing_line_nr_mapping_raises() -> None:
    """
    line 70:
    If 'line_nr' is not mapped, KeyError must be raised.
    """
    print("\n=== TEST CASE 6: Missing line_nr mapping raises ===")
    data = {
        "id": [1],
        "vejx": ["14,71"],
        "vejy": ["55,12"],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
    }
    with pytest.raises(KeyError, match="line_nr"):
        prepare_dataset_for_runner(csv_path, col_map)
    os.remove(csv_path)

def test_case_7_missing_address_fields_raises() -> None:
    """
    line 92:
    Missing address fields should raise KeyError.
    """
    print("\n=== TEST CASE 7: Missing address fields raises ===")
    data = {
        "id": [1],
        "vejx": ["14,71"],
        "vejy": ["55,12"],
        "linienr": [0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "address": {
            "fields": ["street", "city"],
        },
    }
    with pytest.raises(KeyError, match="Address fields missing"):
        prepare_dataset_for_runner(csv_path, col_map)
    os.remove(csv_path)

def test_case_8_missing_type_source_column_raises() -> None:
    """
    line 139:
    If type source column does not exist, KeyError is raised.
    """
    print("\n=== TEST CASE 8: Missing type source column raises ===")
    data = {
        "id": [1],
        "vejx": ["14,71"],
        "vejy": ["55,12"],
        "linienr": [0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "type": {
            "name": "beregning",
            "foot": {"val": 0, "annotations": "distance"},
        },
    }
    with pytest.raises(KeyError, match="Type source column"):
        prepare_dataset_for_runner(csv_path, col_map)
    os.remove(csv_path)

def test_case_9_type_resolution_fallback_defaults() -> None:
    """
    line 150:
    Unknown type values fall back to ('foot', 'distance').
    """
    print("\n=== TEST CASE 9: Type resolution fallback ===")
    data = {
        "id": [1],
        "vejx": ["14,71"],
        "vejy": ["55,12"],
        "linienr": [0],
        "beregning": [99],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "type": {
            "name": "beregning",
            "car": {"val": 1, "annotations": "duration"},
        },
    }
    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    assert df_clean["distance_type"].iloc[0] == "foot"
    assert df_clean["annotation_type"].iloc[0] == "distance"
    os.remove(csv_path)

def test_case_10_problem_type_resolution_all_branches() -> None:
    """
    line 183:
    HPP / OUT:HPP / TSP / OUT:TSP / fallback resolution.
    """
    print("\n=== TEST CASE 10: Problem type resolution ===")
    data = {
        "id": [1, 1, 1, 1, 1],
        "vejx": ["14,71"] * 5,
        "vejy": ["55,12"] * 5,
        "linienr": [0, 1, 2, 3, 4],
        "ptype": [1, 2, 3, 4, 99],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "problem_type": {
            "name": "ptype",
            "HPP": [1],
            "OUT:HPP": [2],
            "TSP": [3],
            "OUT:TSP": [4],
        },
    }
    df_clean = prepare_dataset_for_runner(csv_path, col_map)
    assert df_clean["problem_type"].tolist() == [
        "HPP", "OUT:HPP", "TSP", "OUT:TSP", "TSP"
    ]
    os.remove(csv_path)

def test_case_11_real_dataset_smoke_test() -> None:
    """
    Real dataset test:
    Ensure prepare_dataset_for_runner runs on test_data.csv.
    """
    print("\n=== TEST CASE 11: Real dataset smoke test ===")
    csv_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_data.csv"
    )
    col_map = {"route_id": { "name": "id" },
            "lon":      { "name": "vejx" },
            "lat":      { "name": "vejy" },
            "line_nr":  { "name": "linienr" },
            "address": { 
                "fields": ["adresse"],
                "separator": "; "
            },
            "transform": {
                "convert_from": "EPSG:25832",
                "convert_to":   "EPSG:4326"
            },
            "type": {
                "name": "beregning",
                "foot":  {"val": 0, "annotations": "distance"},
                "car":   {"val": 1, "annotations": "duration"},
                "cycle": {"val": 2, "annotations": "distance"}
            },
            "problem_type": {
                "name": "beregning",
                "HPP": [1],
                "OUT:TSP": [0, 2]
            }
        }
    df = prepare_dataset_for_runner(csv_path, col_map)
    for col in [
        "route_id",
        "lon",
        "lat",
        "line_nr",
        "n_postboxes",
        "distance_type",
        "annotation_type",
        "problem_type",
    ]:
        assert col in df.columns
    assert len(df) > 0

def test_case_12_real_dataset_vector_lon_lat_with_fraction() -> None:
    """
    Real dataset test:
    - Vector-based lon/lat resolution
    - fraction applied
    - EPSG transform applied
    """
    print("\n=== TEST CASE 12: Real dataset vector lon/lat with fraction ===")
    csv_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_data.csv"
    )
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name_from": "husx", "name_to": "vejx"},
        "lat": {"name_from": "husy", "name_to": "vejy"},
        "fraction": 0.9,
        "line_nr": {"name": "linienr"},
        "address": {
            "fields": ["adresse"],
            "separator": "; ",
        },
        "transform": {
            "convert_from": "EPSG:25832",
            "convert_to": "EPSG:4326",
        },
        "type": {
            "name": "beregning",
            "foot": {"val": 0, "annotations": "distance"},
            "car": {"val": 1, "annotations": "duration"},
            "cycle": {"val": 2, "annotations": "distance"},
        },
        "problem_type": {
            "name": "beregning",
            "HPP": [1],
            "OUT:TSP": [0, 2],
        },
    }
    df = prepare_dataset_for_runner(csv_path, col_map)
    print(df.head())
    for col in [
        "route_id",
        "lon",
        "lat",
        "line_nr",
        "n_postboxes",
        "distance_type",
        "annotation_type",
        "problem_type",
    ]:
        assert col in df.columns
    assert df["lon"].between(-180, 180).all()
    assert df["lat"].between(-90, 90).all()
    assert len(df) > 0

def test_case_13_simple_vector_fraction_usage() -> None:
    """
    Simple synthetic dataset:
    - Vector lon/lat computation
    - Explicit fraction usage
    """
    print("\n=== TEST CASE 13: Simple vector fraction usage ===")
    data = {
        "id": [1],
        "linienr": [0],
        "x1": [0.0],
        "y1": [0.0],
        "x2": [10.0],
        "y2": [20.0],
    }
    df_raw = pd.DataFrame(data)
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "line_nr": {"name": "linienr"},
        "lon": {"name_from": "x1", "name_to": "x2"},
        "lat": {"name_from": "y1", "name_to": "y2"},
        "fraction": 0.5,
    }
    df = prepare_dataset_for_runner(csv_path, col_map)
    print(df)
    assert df["lon"].iloc[0] == 5.0
    assert df["lat"].iloc[0] == 10.0
    assert df["distance_type"].iloc[0] == "foot"
    assert df["annotation_type"].iloc[0] == "distance"
    assert df["problem_type"].iloc[0] == "TSP"
    os.remove(csv_path)

def test_case_14_prepare_dataset_with_temp_revenue_csv():
    """
    Synthetic test:
    - temp base CSV
    - temp revenue CSV with duplicate join keys
    - revenue aggregated before AVG
    """
    print("\n=== TEST CASE 14: prepare_dataset_for_runner with temp revenue CSV ===")
    # -----------------------------
    # Base dataset
    # -----------------------------
    df_base = pd.DataFrame({
        "id": [1],
        "vejx": ["10,0"],
        "vejy": ["20,0"],
        "linienr": [0],
        "kommune": [1],
        "vejnr": [100],
        "husnr": [10],
        "husbog": ["A"],
    })
    base_csv = _write_temp_csv(df_base)
    # -----------------------------
    # Revenue dataset (duplicate group)
    # -----------------------------
    rev_df = pd.DataFrame({
        "kommune": [1, 1],
        "vejnr": [100, 100],
        "husnr": [10, 10],
        "husbog": ["A", "A"],
        "w1": [10.0, 30.0],
        "w2": [20.0, 40.0],
    })
    rev_fd, rev_csv = tempfile.mkstemp(suffix=".csv")
    os.close(rev_fd)
    rev_df.to_csv(rev_csv, sep=";", index=False)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "revenue": {
            "path_revenue": rev_csv,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["w1", "w2"],
            "rev_formula": "AVG",
            "rev_include_all_addresses": True,
        },
    }
    df_out = prepare_dataset_for_runner(base_csv, col_map)
    assert "revenue" in df_out.columns
    assert df_out["revenue"].iloc[0] == 50.0
    print("[OK] Revenue aggregated and averaged correctly")
    os.remove(base_csv)
    os.remove(rev_csv)

def test_case_15_prepare_dataset_with_real_revenue_data():
    """
    Real dataset test:
    - test_data.csv + test_revenue_data.csv
    - revenue column added
    - NaNs filled with 0.0
    """
    print("\n=== TEST CASE 15: prepare_dataset_for_runner with real revenue data ===")
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
            "rev_fields": ["week_2536", "week_2537", "week_2538", "week_2539"],
            "rev_formula": "AVG",
            "rev_include_all_addresses": True,
        },
    }
    df_out = prepare_dataset_for_runner(csv_path, col_map)
    assert "revenue" in df_out.columns
    assert df_out["revenue"].dtype == float
    assert df_out["revenue"].isna().sum() == 0
    assert (df_out["revenue"] >= 0.0).all()
    print(df_out.head())
    print("[OK] Revenue attached correctly for real dataset")
    print(df_out[["route_id", "line_nr", "revenue"]].head())

if __name__ == "__main__":
    test_case_1_basic_no_transform()
    test_case_2_with_transform_identity()
    test_case_3_existing_internal_columns_conflict()
    test_case_4_missing_mapped_column_raises()
    test_case_5_type_mapping_to_distance_and_annotation()
    test_case_6_missing_line_nr_mapping_raises()
    test_case_7_missing_address_fields_raises()
    test_case_8_missing_type_source_column_raises()
    test_case_9_type_resolution_fallback_defaults()
    test_case_10_problem_type_resolution_all_branches()
    test_case_11_real_dataset_smoke_test()
    test_case_12_real_dataset_vector_lon_lat_with_fraction()
    test_case_13_simple_vector_fraction_usage()
    test_case_14_prepare_dataset_with_temp_revenue_csv()
    test_case_15_prepare_dataset_with_real_revenue_data()
