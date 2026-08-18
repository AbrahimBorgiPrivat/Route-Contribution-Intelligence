import pandas as pd

from libraries.utils.preprocessing.osrm.osrm_data import (
    extract_structured_nodes_and_coords,
)


def test_extract_structured_nodes_and_coords_basic() -> None:
    """
    Basic structured-route extraction test.

    Verifies:
    - correct ordering per unit
    - correct node typing (start / address / end)
    - correct m_index alignment
    - OSRM-ready location format
    """

    # --------------------------------------------------
    # Example dataframe with two units
    # --------------------------------------------------
    data = {
        "route_nr": [0, 1, 2, 3],
        "lon": [14.71, 14.72, 14.80, 14.81],
        "lat": [55.12, 55.13, 55.20, 55.21],
        "unit_number": [0, 0, 1, 1],
        "unit_start_point_lon": [14.705, 14.705, 14.790, 14.790],
        "unit_start_point_lat": [55.115, 55.115, 55.195, 55.195],
        "unit_end_point_lon":   [14.725, 14.725, 14.830, 14.830],
        "unit_end_point_lat":   [55.135, 55.135, 55.225, 55.225],
    }

    df = pd.DataFrame(data)

    # --------------------------------------------------
    # Run extraction
    # --------------------------------------------------
    locations, nodes = extract_structured_nodes_and_coords(df)

    # --------------------------------------------------
    # Basic structure assertions
    # --------------------------------------------------
    assert isinstance(locations, list)
    assert isinstance(nodes, list)
    assert len(locations) == len(nodes)

    # Expected:
    # unit 0 → start + 2 addresses + end
    # unit 1 → start + 2 addresses + end
    assert len(locations) == 8

    # --------------------------------------------------
    # Location format (OSRM-ready)
    # --------------------------------------------------
    for loc in locations:
        assert set(loc.keys()) == {"lon", "lat"}
        assert isinstance(loc["lon"], float)
        assert isinstance(loc["lat"], float)

    # --------------------------------------------------
    # Node invariants
    # --------------------------------------------------
    for i, node in enumerate(nodes):
        assert node["m_index"] == i
        assert node["type"] in {"start", "address", "end"}
        assert isinstance(node["unit"], int)

        if node["type"] == "address":
            assert isinstance(node["route_number"], int)
        else:
            assert node["route_number"] is None

    # --------------------------------------------------
    # Explicit ordering check (unit 0)
    # --------------------------------------------------
    assert nodes[0]["type"] == "start"
    assert nodes[1]["type"] == "address"
    assert nodes[2]["type"] == "address"
    assert nodes[3]["type"] == "end"

    assert nodes[0]["unit"] == 0
    assert nodes[1]["unit"] == 0
    assert nodes[2]["unit"] == 0
    assert nodes[3]["unit"] == 0

    # --------------------------------------------------
    # Explicit ordering check (unit 1)
    # --------------------------------------------------
    assert nodes[4]["type"] == "start"
    assert nodes[5]["type"] == "address"
    assert nodes[6]["type"] == "address"
    assert nodes[7]["type"] == "end"

    assert nodes[4]["unit"] == 1
    assert nodes[5]["unit"] == 1
    assert nodes[6]["unit"] == 1
    assert nodes[7]["unit"] == 1


if __name__ == "__main__":
    test_extract_structured_nodes_and_coords_basic()
