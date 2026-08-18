import pandas as pd

from libraries.utils.preprocessing.route_data_preparer import _unit_entry_exit_osrm_closest
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable
from libraries.classes.osrm_api import OSRMClient

# ---------------------------------------------------------------------
# TEST 1: Integration test (real OSRM, skippable)
# ---------------------------------------------------------------------
def test_osrm_closest_with_real_service():
    print("\n=== TEST: osrm_closest (REAL OSRM) ===")
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    df = pd.DataFrame(
        {
            "unit_number": [0, 0, 0],
            "route_nr": [0, 1, 2],
            "lon": [12.5683, 12.5690, 12.5700],
            "lat": [55.6761, 55.6768, 55.6772],
            "unit_start_point_lon": [12.5660] * 3,
            "unit_start_point_lat": [55.6750] * 3,
            "unit_end_point_lon": [12.5720] * 3,
            "unit_end_point_lat": [55.6785] * 3,
        }
    )
    print("\nInput dataframe:")
    print(df)
    out = _unit_entry_exit_osrm_closest(
        df.copy(),
        profile="foot",
    )
    print("\nOutput dataframe:")
    print(out)
    assert out["unit_start_point_lon"].nunique() == 1
    assert out["unit_end_point_lon"].nunique() == 1
    assert out.iloc[0]["unit_start_point_lon"] in df["lon"].values
    assert out.iloc[0]["unit_end_point_lon"] in df["lon"].values
    print("[OK] osrm_closest resolved entry/exit using real OSRM")

# ---------------------------------------------------------------------
# TEST 2: Pure unit test (mocked OSRMClient.table)
# ---------------------------------------------------------------------
def test_osrm_closest_without_osrm_service():
    print("\n=== TEST: osrm_closest (MOCKED OSRM) ===")
    # -----------------------------
    # Monkeypatch OSRMClient.table
    # -----------------------------
    def fake_table(self, locations, sources, destinations, annotations):
        """
        Deterministic fake distances:
        distance = index difference
        """
        n_src = len(sources)
        n_dst = len(destinations)
        distances = []
        for i in range(n_src):
            row = []
            for j in range(n_dst):
                row.append(abs(sources[i] - destinations[j]))
            distances.append(row)
        return {"distances": distances}
    original_table = OSRMClient.table
    OSRMClient.table = fake_table
    try:
        df = pd.DataFrame(
            {
                "unit_number": [0, 0, 0],
                "route_nr": [0, 1, 2],
                "lon": [10.0, 20.0, 30.0],
                "lat": [0.0, 0.0, 0.0],
                "unit_start_point_lon": [999.0] * 3,
                "unit_start_point_lat": [999.0] * 3,
                "unit_end_point_lon": [888.0] * 3,
                "unit_end_point_lat": [888.0] * 3,
            }
        )
        print("\nInput dataframe:")
        print(df)
        out = _unit_entry_exit_osrm_closest(
            df.copy(),
            profile="foot",
        )
        print("\nOutput dataframe:")
        print(out)
        assert (out["unit_start_point_lon"] == 10.0).all()
        assert (out["unit_end_point_lon"] == 30.0).all()
        print("[OK] osrm_closest works without OSRM service")
    finally:
        OSRMClient.table = original_table

if __name__ == "__main__":
    test_osrm_closest_with_real_service()
    test_osrm_closest_without_osrm_service()
