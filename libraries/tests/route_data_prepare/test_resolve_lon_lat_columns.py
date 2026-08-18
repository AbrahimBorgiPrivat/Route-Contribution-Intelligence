import pandas as pd
import pytest
import os
from libraries.utils.preprocessing.route_data_preparer import (
    resolve_lon_lat_columns,
)


# ------------------------------------------------------------
# TEST CASE 1: Direct mode basic rename + numeric conversion
# ------------------------------------------------------------
def test_case_1_direct_mode_basic() -> None:
    """
    Direct mode:
    - lon/lat mapped via 'name'
    - comma decimals converted
    """
    print("\n=== TEST CASE 1: Direct mode basic ===")

    df = pd.DataFrame(
        {
            "x": ["12,5", "13,5"],
            "y": ["55,1", "56,1"],
        }
    )

    col_map = {
        "lon": {"name": "x"},
        "lat": {"name": "y"},
    }

    out = resolve_lon_lat_columns(df, col_map)

    assert list(out["lon"]) == [12.5, 13.5]
    assert list(out["lat"]) == [55.1, 56.1]


# ------------------------------------------------------------
# TEST CASE 2: Vector mode default fraction (0.9)
# ------------------------------------------------------------
def test_case_2_vector_mode_default_fraction() -> None:
    """
    Vector mode:
    - default fraction = 0.9
    """
    print("\n=== TEST CASE 2: Vector mode default fraction ===")

    df = pd.DataFrame(
        {
            "lon_a": [0.0],
            "lat_a": [0.0],
            "lon_b": [10.0],
            "lat_b": [10.0],
        }
    )

    col_map = {
        "lon": {"name_from": "lon_a", "name_to": "lon_b"},
        "lat": {"name_from": "lat_a", "name_to": "lat_b"},
    }

    out = resolve_lon_lat_columns(df, col_map)

    assert out["lon"].iloc[0] == 9.0
    assert out["lat"].iloc[0] == 9.0


# ------------------------------------------------------------
# TEST CASE 3: Vector mode custom fraction (> 1.0)
# ------------------------------------------------------------
def test_case_3_vector_mode_fraction_over_100_percent() -> None:
    """
    Vector mode:
    - fraction > 1.0 is allowed
    """
    print("\n=== TEST CASE 3: Vector mode fraction > 1.0 ===")
    df = pd.DataFrame(
        {
            "x1": [0.0],
            "y1": [0.0],
            "x2": [10.0],
            "y2": [10.0],
        }
    )
    col_map = {
        "lon": {"name_from": "x1", "name_to": "x2"},
        "lat": {"name_from": "y1", "name_to": "y2"},
        "fraction": 3.0,
    }
    out = resolve_lon_lat_columns(df, col_map)
    assert out["lon"].iloc[0] == 30.0
    assert out["lat"].iloc[0] == 30.0

# ------------------------------------------------------------
# TEST CASE 4: Vector mode with object columns
# ------------------------------------------------------------
def test_case_4_vector_mode_object_cleanup() -> None:
    """
    Vector mode:
    - object dtype with comma decimals
    """
    print("\n=== TEST CASE 4: Vector mode object cleanup ===")
    df = pd.DataFrame(
        {
            "x1": ["1,0"],
            "y1": ["1,0"],
            "x2": ["3,0"],
            "y2": ["3,0"],
        }
    )
    col_map = {
        "lon": {"name_from": "x1", "name_to": "x2"},
        "lat": {"name_from": "y1", "name_to": "y2"},
        "fraction": 0.5,
    }
    out = resolve_lon_lat_columns(df, col_map)
    assert out["lon"].iloc[0] == 2.0
    assert out["lat"].iloc[0] == 2.0

# ------------------------------------------------------------
# TEST CASE 5: Missing lon/lat configuration
# ------------------------------------------------------------
def test_case_5_missing_lon_lat_config_raises() -> None:
    """
    Missing lon or lat in col_map should raise KeyError.
    """
    print("\n=== TEST CASE 5: Missing lon/lat config raises ===")
    df = pd.DataFrame({"x": [1], "y": [2]})
    with pytest.raises(KeyError):
        resolve_lon_lat_columns(df, col_map={})

# ------------------------------------------------------------
# TEST CASE 6: Ambiguous configuration (direct + vector)
# ------------------------------------------------------------
def test_case_6_ambiguous_lon_lat_config_raises() -> None:
    """
    Both direct and vector config defined → ValueError.
    """
    print("\n=== TEST CASE 6: Ambiguous lon/lat config raises ===")
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    col_map = {
        "lon": {"name": "a", "name_from": "a", "name_to": "c"},
        "lat": {"name": "b", "name_from": "b", "name_to": "d"},
    }
    with pytest.raises(ValueError):
        resolve_lon_lat_columns(df, col_map)

# ------------------------------------------------------------
# TEST CASE 7: Invalid configuration (neither mode)
# ------------------------------------------------------------
def test_case_7_invalid_lon_lat_config_raises() -> None:
    """
    Neither direct nor vector mode configured → ValueError.
    """
    print("\n=== TEST CASE 7: Invalid lon/lat config raises ===")
    df = pd.DataFrame({"x": [1], "y": [2]})
    col_map = {
        "lon": {},
        "lat": {},
    }
    with pytest.raises(ValueError):
        resolve_lon_lat_columns(df, col_map)

# ------------------------------------------------------------
# TEST CASE 8: Missing vector source columns
# ------------------------------------------------------------
def test_case_8_missing_vector_columns_raises() -> None:
    """
    Vector mode with missing source columns → KeyError.
    """
    print("\n=== TEST CASE 8: Missing vector columns raises ===")
    df = pd.DataFrame({"x1": [0], "y1": [0]})
    col_map = {
        "lon": {"name_from": "x1", "name_to": "x2"},
        "lat": {"name_from": "y1", "name_to": "y2"},
    }
    with pytest.raises(KeyError):
        resolve_lon_lat_columns(df, col_map)
# ------------------------------------------------------------
# TEST CASE 9: EPSG transform path exercised
# ------------------------------------------------------------
def test_case_9_epsg_transform_applied() -> None:
    """
    EPSG transform:
    - 4326 -> 4326 (identity)
    """
    print("\n=== TEST CASE 9: EPSG transform applied ===")
    df = pd.DataFrame(
        {
            "x": [12.0],
            "y": [55.0],
        }
    )
    col_map = {
        "lon": {"name": "x"},
        "lat": {"name": "y"},
        "transform": {
            "convert_from": "EPSG:4326",
            "convert_to": "EPSG:4326",
        },
    }
    out = resolve_lon_lat_columns(df, col_map)
    assert out["lon"].iloc[0] == 12.0
    assert out["lat"].iloc[0] == 55.0

# ------------------------------------------------------------
# TEST CASE 10: Real dataset – direct lon/lat mapping
# ------------------------------------------------------------
def test_case_10_real_data_direct_mode() -> None:
    """
    Real dataset:
    - Direct lon/lat mapping
    - No vector math
    - No transform
    """
    print("\n=== TEST CASE 10: Real data direct lon/lat ===")

    csv_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_data.csv"
    )

    df = pd.read_csv(csv_path, sep=";")

    col_map = {
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
    }
    out = resolve_lon_lat_columns(df, col_map)
    assert "lon" in out.columns
    assert "lat" in out.columns
    assert out["lon"].dtype == float
    assert out["lat"].dtype == float
    assert out["lon"].notna().all()
    assert out["lat"].notna().all()

# ------------------------------------------------------------
# TEST CASE 11: Real dataset – vector mode + transform
# ------------------------------------------------------------
def test_case_11_real_data_vector_mode_with_transform() -> None:
    """
    Real dataset:
    - Vector lon/lat computation
    - fraction = 0.9
    - EPSG:25832 → EPSG:4326 transform
    """
    print("\n=== TEST CASE 11: Real data vector mode with transform ===")

    csv_path = os.path.join(
        "libraries", "tests", "_test_dataset", "test_data.csv"
    )
    df = pd.read_csv(csv_path, sep=";")
    col_map = {
        "lon": {"name_from": "husx", "name_to": "vejx"},
        "lat": {"name_from": "husy", "name_to": "vejy"},
        "fraction": 0.9,
        "transform": {
            "convert_from": "EPSG:25832",
            "convert_to": "EPSG:4326",
        },
    }
    out = resolve_lon_lat_columns(df, col_map)
    assert "lon" in out.columns
    assert "lat" in out.columns
    assert out["lon"].between(-180, 180).all()
    assert out["lat"].between(-90, 90).all()
    assert out["lon"].notna().all()
    assert out["lat"].notna().all()
    assert out["lon"].dtype == float
    assert out["lat"].dtype == float

# ------------------------------------------------------------
# MAIN (manual execution)
# ------------------------------------------------------------
if __name__ == "__main__":
    test_case_1_direct_mode_basic()
    test_case_2_vector_mode_default_fraction()
    test_case_3_vector_mode_fraction_over_100_percent()
    test_case_4_vector_mode_object_cleanup()
    test_case_5_missing_lon_lat_config_raises()
    test_case_6_ambiguous_lon_lat_config_raises()
    test_case_7_invalid_lon_lat_config_raises()
    test_case_8_missing_vector_columns_raises()
    test_case_9_epsg_transform_applied()
    test_case_10_real_data_direct_mode()
    test_case_11_real_data_vector_mode_with_transform()