def test_get_turns_from_segment(client):
    snap_payload = {
        "x": 863994,
        "y": 6123307,
        "input_crs": "EPSG:25832",
        "output_crs": "EPSG:4326",
        "allowed_highways": ["residential"],
    }

    snap = client.post("/snap/nearest", json=snap_payload).json()
    segment_id = snap["segment"]["segment_id"]

    r = client.get(f"/segments/{segment_id}/turns")
    assert r.status_code == 200

    turns = r.json()
    assert isinstance(turns, list)

    if turns:
        t = turns[0]
        assert t["from_segment"] == segment_id
        assert "to_segment" in t