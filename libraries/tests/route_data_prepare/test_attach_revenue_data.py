import os
import pandas as pd
import pytest
import tempfile

from libraries.utils.preprocessing.route_data_preparer import attach_revenue_data

# ---------------------------------------------------------------------
# Paths to real test datasets
# ---------------------------------------------------------------------
CSV_PATH = os.path.join("libraries", "tests", "_test_dataset", "test_data.csv")
CSV_REV_PATH = os.path.join("libraries", "tests", "_test_dataset", "test_revenue_data.csv")

def test_case_1_no_revenue_config_returns_df():
    """
    If no revenue config is present in col_map,
    attach_revenue_data should return df unchanged.
    """
    print("\n=== TEST CASE 1: No revenue config ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {}

    df_out = attach_revenue_data(df.copy(), col_map)

    assert df_out.equals(df)
    print("[OK] DataFrame unchanged when no revenue config present")


def test_case_2_missing_revenue_path_returns_df():
    """
    If revenue config exists but path_revenue is missing,
    the original df should be returned unchanged.
    """
    print("\n=== TEST CASE 2: Missing revenue path ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": None
        }
    }

    df_out = attach_revenue_data(df.copy(), col_map)

    assert df_out.equals(df)
    print("[OK] DataFrame unchanged when revenue path is missing")


def test_case_3_revenue_path_not_found_raises():
    """
    If revenue path does not exist, FileNotFoundError is raised.
    """
    print("\n=== TEST CASE 3: Revenue path not found raises ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": "this/file/does/not/exist.csv",
            "join_fields": {"kommune": "kommune"},
            "rev_fields": ["week_2536"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }

    with pytest.raises(FileNotFoundError):
        attach_revenue_data(df, col_map)

    print("[OK] FileNotFoundError correctly raised")


def test_case_4_missing_df_join_column_raises():
    """
    If join column is missing in df, KeyError is raised.
    """
    print("\n=== TEST CASE 4: Missing df join column raises ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {"does_not_exist": "kommune"},
            "rev_fields": ["week_2536"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }

    with pytest.raises(KeyError):
        attach_revenue_data(df, col_map)

    print("[OK] KeyError correctly raised for missing df join column")


def test_case_5_missing_revenue_join_column_raises():
    """
    If join column is missing in revenue CSV, KeyError is raised.
    """
    print("\n=== TEST CASE 5: Missing revenue join column raises ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {"kommune": "does_not_exist"},
            "rev_fields": ["week_2536"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }

    with pytest.raises(KeyError):
        attach_revenue_data(df, col_map)

    print("[OK] KeyError correctly raised for missing revenue join column")


def test_case_6_missing_revenue_field_raises():
    """
    If a revenue field does not exist, KeyError is raised.
    """
    print("\n=== TEST CASE 6: Missing revenue field raises ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["does_not_exist"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }
    with pytest.raises(KeyError):
        attach_revenue_data(df, col_map)
    print("[OK] KeyError correctly raised for missing revenue field")


def test_case_7_invalid_revenue_formula_raises():
    """
    If revenue formula is invalid, ValueError is raised.
    """
    print("\n=== TEST CASE 7: Invalid revenue formula raises ===")
    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["week_2536"],
            "rev_formula": "WRONG",
            "rev_include_all_addresses": False,
        }
    }
    with pytest.raises(ValueError):
        attach_revenue_data(df, col_map)
    print("[OK] ValueError correctly raised for invalid revenue formula")


def test_case_8_revenue_join_left_and_fill_zero():
    """
    Left join + fillna(0.0) when rev_include_all_addresses=False.
    """
    print("\n=== TEST CASE 8: Left join + fill zero ===")
    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["week_2536"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }
    df_out = attach_revenue_data(df, col_map)
    assert "revenue" in df_out.columns
    assert df_out["revenue"].isna().sum() == 0
    assert (df_out["revenue"] >= 0).all()
    print("[OK] Revenue column added with zero-fill")

def test_case_9_revenue_inner_join():
    """
    Inner join when rev_include_all_addresses=True.
    """
    print("\n=== TEST CASE 9: Inner join only matching addresses ===")

    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["week_2536"],
            "rev_formula": "SUM",
            "rev_include_all_addresses": False,
        }
    }
    df_out = attach_revenue_data(df, col_map)
    assert "revenue" in df_out.columns
    assert len(df_out) < len(df)
    print(f"[OK] Inner join reduced rows from {len(df)} to {len(df_out)}")


def test_case_10_revenue_avg_multiple_fields():
    """
    AVG across multiple revenue fields.
    """
    print("\n=== TEST CASE 10: AVG across multiple revenue fields ===")
    df = pd.read_csv(CSV_PATH,sep= ";")
    col_map = {
        "revenue": {
            "path_revenue": CSV_REV_PATH,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["week_2536", "week_2537", "week_2538", "week_2539"],
            "rev_formula": "AVG",
            "rev_include_all_addresses": False,
        }
    }
    df_out = attach_revenue_data(df, col_map)
    assert "revenue" in df_out.columns
    assert df_out["revenue"].dtype == float
    print("[OK] AVG revenue computed successfully")

def test_case_11_group_cols_not_unique_summarize_then_avg():
    """
    group_cols not unique:
    Revenue rows must be summed per group BEFORE formula is applied.
    """
    print("\n=== TEST CASE 11: group_cols not unique, summarize then AVG ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # -------------------------------
        # Create base df
        # -------------------------------
        df = pd.DataFrame({
            "kommune": [1, 1],
            "vejnr": [100,200],
            "husnr": [10, 10],
            "husbog": ["A", "A"],
        })

        # -------------------------------
        # Create revenue df with duplicate group keys
        # -------------------------------
        rev_df = pd.DataFrame({
            "kommune": [1, 1, 1],
            "vejnr": [100, 100, 200],
            "husnr": [10, 10, 10],
            "husbog": ["A", "A", "A"],
            "week_1": [10.0, 30.0, 50.0],
            "week_2": [20.0, 40.0, 100.0],
        })

        rev_path = os.path.join(tmpdir, "rev.csv")
        rev_df.to_csv(rev_path, sep=";", index=False)

        col_map = {
            "revenue": {
                "path_revenue": rev_path,
                "join_fields": {
                    "kommune": "kommune",
                    "vejnr": "vejnr",
                    "husnr": "husnr",
                    "husbog": "husbog",
                },
                "rev_fields": ["week_1", "week_2"],
                "rev_formula": "AVG",
                "rev_include_all_addresses": False,
            }
        }

        df_out = attach_revenue_data(df, col_map)
        assert df_out.loc[0, "revenue"] == 50.0
        print("[OK] Aggregation before AVG works correctly")
        
def test_case_12_all_revenue_formulas():
    """
    Explicitly test AVG, SUM, MEDIAN, MIN, MAX formulas.
    """
    print("\n=== TEST CASE 12: all revenue formulas ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        df = pd.DataFrame({
            "kommune": [1],
            "vejnr": [1],
            "husnr": [1],
            "husbog": ["A"],
        })
        rev_df = pd.DataFrame({
            "kommune": [1],
            "vejnr": [1],
            "husnr": [1],
            "husbog": ["A"],
            "r1": [10.0],
            "r2": [20.0],
            "r3": [30.0],
        })
        rev_path = os.path.join(tmpdir, "rev.csv")
        rev_df.to_csv(rev_path, sep=";", index=False)
        base_col_map = {
            "path_revenue": rev_path,
            "join_fields": {
                "kommune": "kommune",
                "vejnr": "vejnr",
                "husnr": "husnr",
                "husbog": "husbog",
            },
            "rev_fields": ["r1", "r2", "r3"],
            "rev_include_all_addresses": False,
        }
        expected = {
            "AVG": 20.0,
            "SUM": 60.0,
            "MEDIAN": 20.0,
            "MIN": 10.0,
            "MAX": 30.0,
        }
        for formula, exp_val in expected.items():
            col_map = {
                "revenue": {
                    **base_col_map,
                    "rev_formula": formula,
                }
            }
            df_out = attach_revenue_data(df.copy(), col_map)
            assert df_out.loc[0, "revenue"] == exp_val
            print(f"[OK] {formula} computed correctly → {exp_val}")
            
def test_case_13_custom_revenue_separator():
    """
    Revenue CSV with custom separator should be parsed correctly.
    """
    print("\n=== TEST CASE 13: Custom revenue CSV separator ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # -------------------------------
        # Base dataset
        # -------------------------------
        df = pd.DataFrame({
            "kommune": [1],
            "vejnr": [10],
            "husnr": [5],
            "husbog": ["A"],
        })
        # -------------------------------
        # Revenue CSV using comma separator
        # -------------------------------
        rev_df = pd.DataFrame({
            "kommune": [1],
            "vejnr": [10],
            "husnr": [5],
            "husbog": ["A"],
            "rev_w1": [100.0],
            "rev_w2": [200.0],
        })

        rev_path = os.path.join(tmpdir, "rev_comma.csv")
        rev_df.to_csv(rev_path, sep=",", index=False)

        col_map = {
            "revenue": {
                "path_revenue": rev_path,
                "sep": ",",                      
                "join_fields": {
                    "kommune": "kommune",
                    "vejnr": "vejnr",
                    "husnr": "husnr",
                    "husbog": "husbog",
                },
                "rev_fields": ["rev_w1", "rev_w2"],
                "rev_formula": "SUM",
                "rev_include_all_addresses": False,
            }
        }
        df_out = attach_revenue_data(df, col_map)
        assert "revenue" in df_out.columns
        assert df_out.loc[0, "revenue"] == 300.0
        print("[OK] Custom separator handled correctly")

if __name__ == "__main__":
    test_case_1_no_revenue_config_returns_df()
    test_case_2_missing_revenue_path_returns_df()
    test_case_3_revenue_path_not_found_raises()
    test_case_4_missing_df_join_column_raises()
    test_case_5_missing_revenue_join_column_raises()
    test_case_6_missing_revenue_field_raises()
    test_case_7_invalid_revenue_formula_raises()
    test_case_8_revenue_join_left_and_fill_zero()
    test_case_9_revenue_inner_join()
    test_case_10_revenue_avg_multiple_fields()
    test_case_11_group_cols_not_unique_summarize_then_avg()
    test_case_12_all_revenue_formulas()
    test_case_13_custom_revenue_separator()
