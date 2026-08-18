def test_snap_nearest_returns_valid_segment(snap_index):
    res = snap_index.snap_nearest(
        x=863994,
        y=6123307,
        input_crs="EPSG:25832",
        output_crs="EPSG:4326",
        allowed_highways={
            "residential",
            "secondary",
            "tertiary",
            "primary",
        },
    )
    segment = res["segment"]
    geometry = res["geometry"]
    assert segment["segment_id"] > 0
    assert segment["entry_node"] != segment["exit_node"]
    assert geometry["side_of_road"] in {"left", "right", "center"}
    assert geometry["crs"] == "EPSG:4326"