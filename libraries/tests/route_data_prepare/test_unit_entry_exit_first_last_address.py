import pandas as pd

from libraries.utils.preprocessing.route_data_preparer import (
    _unit_entry_exit_first_last_address,
)


def test_first_last_address_single_unit():
    print("\n=== TEST: first_last_address – single unit ===")

    df = pd.DataFrame(
        {
            "unit_number": [0, 0, 0],
            "route_nr": [0, 1, 2],
            "lon": [10.0, 11.0, 12.0],
            "lat": [50.0, 51.0, 52.0],
            "unit_start_point_lon": [0.0, 0.0, 0.0],
            "unit_start_point_lat": [0.0, 0.0, 0.0],
            "unit_end_point_lon": [99.0, 99.0, 99.0],
            "unit_end_point_lat": [99.0, 99.0, 99.0],
        }
    )

    out = _unit_entry_exit_first_last_address(df.copy())

    print(out)

    assert (out["unit_start_point_lon"] == 10.0).all()
    assert (out["unit_start_point_lat"] == 50.0).all()
    assert (out["unit_end_point_lon"] == 12.0).all()
    assert (out["unit_end_point_lat"] == 52.0).all()

    print("[OK] Single unit resolved correctly")


def test_first_last_address_multiple_units_independent():
    print("\n=== TEST: first_last_address – multiple units ===")

    df = pd.DataFrame(
        {
            "unit_number": [0, 0, 1, 1],
            "route_nr": [1, 0, 3, 2],
            "lon": [11.0, 10.0, 21.0, 20.0],
            "lat": [51.0, 50.0, 61.0, 60.0],
            "unit_start_point_lon": [0.0] * 4,
            "unit_start_point_lat": [0.0] * 4,
            "unit_end_point_lon": [99.0] * 4,
            "unit_end_point_lat": [99.0] * 4,
        }
    )

    out = _unit_entry_exit_first_last_address(df.copy())
    print(out)

    u0 = out[out["unit_number"] == 0]
    u1 = out[out["unit_number"] == 1]

    assert (u0["unit_start_point_lon"] == 10.0).all()
    assert (u0["unit_end_point_lon"] == 11.0).all()

    assert (u1["unit_start_point_lon"] == 20.0).all()
    assert (u1["unit_end_point_lon"] == 21.0).all()

    print("[OK] Units resolved independently")


def test_first_last_address_single_address_unit():
    print("\n=== TEST: first_last_address – single-address unit ===")

    df = pd.DataFrame(
        {
            "unit_number": [0],
            "route_nr": [0],
            "lon": [42.0],
            "lat": [7.0],
            "unit_start_point_lon": [0.0],
            "unit_start_point_lat": [0.0],
            "unit_end_point_lon": [99.0],
            "unit_end_point_lat": [99.0],
        }
    )

    out = _unit_entry_exit_first_last_address(df.copy())
    print(out)

    assert out.loc[0, "unit_start_point_lon"] == 42.0
    assert out.loc[0, "unit_end_point_lon"] == 42.0
    assert out.loc[0, "unit_start_point_lat"] == 7.0
    assert out.loc[0, "unit_end_point_lat"] == 7.0

    print("[OK] Single-address unit handled correctly")


def test_first_last_address_does_not_modify_address_coordinates():
    print("\n=== TEST: first_last_address – does not modify lon/lat ===")

    df = pd.DataFrame(
        {
            "unit_number": [0, 0],
            "route_nr": [0, 1],
            "lon": [1.0, 2.0],
            "lat": [3.0, 4.0],
            "unit_start_point_lon": [10.0, 10.0],
            "unit_start_point_lat": [20.0, 20.0],
            "unit_end_point_lon": [30.0, 30.0],
            "unit_end_point_lat": [40.0, 40.0],
        }
    )

    out = _unit_entry_exit_first_last_address(df.copy())
    print(out)
    assert list(out["lon"]) == [1.0, 2.0]
    assert list(out["lat"]) == [3.0, 4.0]

if __name__ == "__main__":
    test_first_last_address_single_unit()
    test_first_last_address_multiple_units_independent()
    test_first_last_address_single_address_unit()
    test_first_last_address_does_not_modify_address_coordinates()
