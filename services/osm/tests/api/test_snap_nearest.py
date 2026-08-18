def test_snap_nearest_basic(client):
    payload = {
        "x": 863994,
        "y": 6123307,
        "input_crs": "EPSG:25832",
        "output_crs": "EPSG:4326",
        "allowed_highways": [
            "residential",
            "secondary",
            "tertiary",
        ],
    }

    r = client.post("/snap/nearest", json=payload)
    assert r.status_code == 200

    data = r.json()

    # Input
    assert data["input"]["crs"] == "EPSG:25832"

    # Segment
    segment = data["segment"]
    assert segment["segment_id"] > 0
    assert "entry_node" in segment
    assert "exit_node" in segment

    # Projection
    proj = data["projected_point"]
    assert proj["crs"] == "EPSG:4326"
    assert -180 <= proj["x"] <= 180
    assert -90 <= proj["y"] <= 90

    # Geometry
    geom = data["geometry"]
    assert geom["side_of_road"] in {"left", "right", "center"}