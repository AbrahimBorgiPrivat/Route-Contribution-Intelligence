import pandas as pd

from libraries.utils.preprocessing.route_data_preparer import (
    _apply_unit_entry_exit_strategy,
)
from libraries.tests._utils.skip_if_service_down import (
    skip_if_service_unavailable,
)
from libraries.classes.osrm_api import OSRMClient


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _base_df():
    """
    Base dataframe used by multiple tests.
    """
    return pd.DataFrame(
        {
            "unit_number": [0, 0, 0],
            "route_nr": [0, 1, 2],
            "lon": [10.0, 20.0, 30.0],
            "lat": [50.0, 51.0, 52.0],
            "unit_start_point_lon": [10.1, 10.1, 10.1],
            "unit_start_point_lat": [50.1, 50.1, 50.1],
            "unit_end_point_lon": [50.9, 50.9, 50.9],
            "unit_end_point_lat": [50.9, 50.9, 50.9],
        }
    )


# ---------------------------------------------------------------------
# TEST 1: None / SNAPPED → no-op
# ---------------------------------------------------------------------
def test_apply_strategy_none_and_snapped_noop():
    print("\n=== TEST: apply strategy NONE / SNAPPED (no-op) ===")

    df = _base_df()
    df_orig = df.copy(deep=True)

    out_none = _apply_unit_entry_exit_strategy(
        df.copy(),
        strategy=None,
        osrm_profile="foot",
    )

    out_snapped = _apply_unit_entry_exit_strategy(
        df.copy(),
        strategy="SNAPPED",
        osrm_profile="foot",
    )

    print("\nOriginal:")
    print(df_orig)
    print("\nAfter NONE:")
    print(out_none)
    print("\nAfter SNAPPED:")
    print(out_snapped)

    pd.testing.assert_frame_equal(out_none, df_orig)
    pd.testing.assert_frame_equal(out_snapped, df_orig)

    print("[OK] NONE and SNAPPED leave dataframe unchanged")


# ---------------------------------------------------------------------
# TEST 2: FIRST_LAST_ADDRESS
# ---------------------------------------------------------------------
def test_apply_strategy_first_last_address():
    print("\n=== TEST: apply strategy FIRST_LAST_ADDRESS ===")

    df = _base_df()

    out = _apply_unit_entry_exit_strategy(
        df.copy(),
        strategy="FIRST_LAST_ADDRESS",
        osrm_profile="foot",
    )

    print("\nResult:")
    print(out)

    assert (out["unit_start_point_lon"] == 10.0).all()
    assert (out["unit_start_point_lat"] == 50.0).all()
    assert (out["unit_end_point_lon"] == 30.0).all()
    assert (out["unit_end_point_lat"] == 52.0).all()

    print("[OK] FIRST_LAST_ADDRESS applied correctly")


# ---------------------------------------------------------------------
# TEST 3: OSRM_CLOSEST (real service, skippable)
# ---------------------------------------------------------------------
def test_apply_strategy_osrm_closest_real_service():
    print("\n=== TEST: apply strategy OSRM_CLOSEST (REAL OSRM) ===")

    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )

    df = _base_df()

    out = _apply_unit_entry_exit_strategy(
        df.copy(),
        strategy="OSRM_CLOSEST",
        osrm_profile="foot",
    )

    print("\nResult:")
    print(out)

    # Entry / exit must be selected from addresses
    assert out["unit_start_point_lon"].iloc[0] in df["lon"].values
    assert out["unit_end_point_lon"].iloc[0] in df["lon"].values

    print("[OK] OSRM_CLOSEST resolved using real OSRM")


# ---------------------------------------------------------------------
# TEST 4: OSRM_CLOSEST (mocked OSRM, always runs)
# ---------------------------------------------------------------------
def test_apply_strategy_osrm_closest_mocked():
    print("\n=== TEST: apply strategy OSRM_CLOSEST (MOCKED OSRM) ===")

    def fake_table(self, locations, sources, destinations, annotations):
        # deterministic fake distances
        distances = []
        for i in sources:
            row = []
            for j in destinations:
                row.append(abs(i - j))
            distances.append(row)
        return {"distances": distances}

    original_table = OSRMClient.table
    OSRMClient.table = fake_table

    try:
        df = _base_df()

        out = _apply_unit_entry_exit_strategy(
            df.copy(),
            strategy="OSRM_CLOSEST",
            osrm_profile="foot",
        )

        print("\nResult:")
        print(out)

        # Deterministic outcome with fake distances:
        # start → index 0, end → index 2
        assert (out["unit_start_point_lon"] == 10.0).all()
        assert (out["unit_end_point_lon"] == 30.0).all()

        print("[OK] OSRM_CLOSEST works with mocked OSRM")

    finally:
        OSRMClient.table = original_table


# ---------------------------------------------------------------------
# TEST 5: Invalid strategy
# ---------------------------------------------------------------------
def test_apply_strategy_invalid_value():
    print("\n=== TEST: apply strategy INVALID VALUE ===")

    df = _base_df()

    try:
        _apply_unit_entry_exit_strategy(
            df.copy(),
            strategy="INVALID_STRATEGY",
            osrm_profile="foot",
        )
    except ValueError as e:
        print("Caught expected ValueError:")
        print(e)
        assert "Invalid unit_entry_exit_strategy" in str(e)
    else:
        raise AssertionError("Expected ValueError not raised")
    print("[OK] Invalid strategy correctly rejected")

# ---------------------------------------------------------------------
# Executable entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    test_apply_strategy_none_and_snapped_noop()
    test_apply_strategy_first_last_address()
    test_apply_strategy_osrm_closest_real_service()
    test_apply_strategy_osrm_closest_mocked()
    test_apply_strategy_invalid_value()
