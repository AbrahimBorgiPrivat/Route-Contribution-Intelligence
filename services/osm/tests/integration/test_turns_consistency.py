def test_turns_reference_valid_segments(snap_index):
    res = snap_index.snap_nearest(
        x=863994,
        y=6123307,
        input_crs="EPSG:25832",
    )
    sid = res["segment"]["segment_id"]
    turns = snap_index.get_turns_from_segment(sid)
    for t in turns:
        assert t["from_segment"] == sid
        assert t["to_segment"] in snap_index.state.geom_by_segment_id
        assert t["node"] in (
            res["segment"]["entry_node"],
            res["segment"]["exit_node"],
        )
