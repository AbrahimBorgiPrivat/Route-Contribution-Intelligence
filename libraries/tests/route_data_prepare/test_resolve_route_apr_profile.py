import pandas as pd
import pytest
from libraries.utils.preprocessing.route_data_preparer import resolve_route_apr_profile

def test_case_1_basic_resolution() -> None:
    """
    Basic test:
    - single route
    - unique distance_type and annotation_type
    - APR exists
    """
    print("\n=== TEST CASE 1: Basic resolve_route_apr_profile ===")

    data = {
        "distance_type": ["foot", "foot", "foot"],
        "annotation_type": ["distance", "distance", "distance"],
    }
    df = pd.DataFrame(data)
    APR = {
        "foot": {
            "distance": 0.03,
        }
    }
    result = resolve_route_apr_profile(df, APR)
    print("[RESULT]", result)
    assert result["profile"] == "foot"
    assert result["annotation"] == "distance"
    assert result["APR"] == 0.03
    assert result["unit"] == "m"

def test_case_2_mixed_distance_type_raises() -> None:
    """
    If multiple distance_type values exist in one route, raise ValueError.
    """
    print("\n=== TEST CASE 2: Mixed distance_type raises ===")
    data = {
        "distance_type": ["foot", "car"],
        "annotation_type": ["distance", "distance"],
    }
    df = pd.DataFrame(data)
    APR = {
        "foot": {"distance": 0.03},
        "car": {"distance": 0.04},
    }
    with pytest.raises(ValueError):
        resolve_route_apr_profile(df, APR)


def test_case_3_mixed_annotation_type_raises() -> None:
    """
    If multiple annotation_type values exist in one route, raise ValueError.
    """
    print("\n=== TEST CASE 3: Mixed annotation_type raises ===")

    data = {
        "distance_type": ["foot", "foot"],
        "annotation_type": ["distance", "duration"],
    }
    df = pd.DataFrame(data)
    APR = {
        "foot": {
            "distance": 0.03,
            "duration": 0.05,
        }
    }
    with pytest.raises(ValueError):
        resolve_route_apr_profile(df, APR)


def test_case_4_missing_apr_definition_raises() -> None:
    """
    If APR[profile][annotation] does not exist, raise KeyError.
    """
    print("\n=== TEST CASE 4: Missing APR mapping raises ===")
    data = {
        "distance_type": ["car"],
        "annotation_type": ["duration"],
    }
    df = pd.DataFrame(data)

    APR = {
        "car": {
            "distance": 0.04,  # duration missing
        }
    }
    with pytest.raises(KeyError):
        resolve_route_apr_profile(df, APR)


def test_case_5_unknown_annotation_defaults_unit_seconds() -> None:
    """
    Sanity check: annotation != 'distance' → unit is seconds.
    """
    print("\n=== TEST CASE 5: Unit resolution ===")
    data = {
        "distance_type": ["car"],
        "annotation_type": ["duration"],
    }
    df = pd.DataFrame(data)
    APR = {
        "car": {
            "duration": 0.04,
        }
    }
    result = resolve_route_apr_profile(df, APR)
    assert result["unit"] == "sec"
    
if __name__ == "__main__":
    test_case_1_basic_resolution()
    test_case_2_mixed_distance_type_raises()
    test_case_3_mixed_annotation_type_raises()
    test_case_4_missing_apr_definition_raises()
    test_case_5_unknown_annotation_defaults_unit_seconds()
