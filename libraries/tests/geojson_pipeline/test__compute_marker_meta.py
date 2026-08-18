import numpy as np
from libraries.utils.visualization.geojson_pipeline import _compute_marker_meta

def test_compute_marker_meta_scalar_E():
    route_id = "42"
    locations = [
        {"route_nr": 0, "n_postboxes": 2, "address": "Addr A"},
        {"route_nr": 1, "n_postboxes": 3, "address": "Addr B"},
    ]
    E = 5.0
    meta = _compute_marker_meta(
        route_id=route_id,
        locations=locations,
        E=E,
    )
    assert isinstance(meta, dict)
    assert set(meta.keys()) == {0, 1}
    assert meta[0]["route_id"] == route_id
    assert meta[0]["postboxes"] == 2
    assert meta[0]["revenue"] == 10.0  
    assert meta[0]["address"] == "Addr A"
    assert meta[1]["postboxes"] == 3
    assert meta[1]["revenue"] == 15.0  
    assert meta[1]["address"] == "Addr B"


def test_compute_marker_meta_list_E():
    route_id = "7"
    locations = [
        {"route_nr": 0, "n_postboxes": 1, "address": "A"},
        {"route_nr": 1, "n_postboxes": 2, "address": "B"},
        {"route_nr": 2, "n_postboxes": 3, "address": "C"},
    ]
    E = [1.5, 2.0, 2.5]
    meta = _compute_marker_meta(
        route_id=route_id,
        locations=locations,
        E=E,
    )
    assert meta[0]["revenue"] == 1.5
    assert meta[1]["revenue"] == 4.0  
    assert meta[2]["revenue"] == 7.5  

def test_compute_marker_meta_numpy_E():
    route_id = "99"
    locations = [
        {"route_nr": 0, "n_postboxes": 2, "address": "X"},
        {"route_nr": 1, "n_postboxes": 1, "address": "Y"},
    ]
    E = np.array([3.0, 4.0])
    meta = _compute_marker_meta(
        route_id=route_id,
        locations=locations,
        E=E,
    )
    assert meta[0]["revenue"] == 6.0   
    assert meta[1]["revenue"] == 4.0   

def test_compute_marker_meta_default_postboxes():
    """
    n_postboxes should default to 1 if missing.
    """
    route_id = "100"
    locations = [
        {"route_nr": 0, "address": "No PB"},
    ]
    E = 2.25
    meta = _compute_marker_meta(
        route_id=route_id,
        locations=locations,
        E=E,
    )
    assert meta[0]["postboxes"] == 1
    assert meta[0]["revenue"] == 2.25


def test_compute_marker_meta_rounding():
    """
    Revenue should be rounded to 2 decimals.
    """
    route_id = "round"
    locations = [
        {"route_nr": 0, "n_postboxes": 3, "address": "R"},
    ]
    E = 1.333333
    meta = _compute_marker_meta(
        route_id=route_id,
        locations=locations,
        E=E,
    )
    assert meta[0]["revenue"] == 4.0
