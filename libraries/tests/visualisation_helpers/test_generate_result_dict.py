import pytest
from pprint import pprint
from libraries.utils.visualization.visualisation_helpers import generate_result_dict   

KPI_MAPPING = [
    {"name": "Rute ID",
     "key": "route_id",
     "type": "both",
     "val": lambda r: r["route_id"]},
    {"name": "T1 DG original",
     "key": "t1_DG_org",
     "type": "type1",
     "val": lambda r: r["DG_original"]},
    {"name": "T1 DG best",
     "key": "t1_DG_best",
     "type": "type1",
     "val": lambda r: r["DG_best"]},
    {"name": "T1 Outliers",
     "key": "t1_seg_outliers",
     "type": "type1",
     "val": lambda r: len(r["S_outlier"])},
    {"name": "T2 DG best",
     "key": "t2_DG_best",
     "type": "type2",
     "val": lambda r: r["DG_best"]},
    {"name": "T2 Outliers",
     "key": "t2_seg_outliers",
     "type": "type2",
     "val": lambda r: len(r["S_outlier"])},
    {"name": "Metode",
     "key": "t2_solver",
     "type": "type2",
     "val": lambda r: r["solver"]},
]

RESULT_ROWS = [
    {
        "strict_order": True,        
        "route_id": "A12",
        "DG_original": 100.0,
        "DG_best": 120.0,
        "L_original": 500.0,
        "L_opt": 470.0,
        "S_outlier": [2, 5],
        "C2_max": 10.1,
        "solver": "python_tsp"
    },
    {
        "strict_order": False,       
        "route_id": "A12",
        "DG_original": None,
        "DG_best": 140.0,
        "L_original": None,
        "L_opt": 450.0,
        "S_outlier": [5],
        "C2_max": 12.5,
        "solver": "lkh"
    }
]

def test_generate_both_types_ok():
    """Test extraction with route_type = 'both'."""
    all_results = []
    route_type = "both"
    all_results, kpis = generate_result_dict(
        route_id="A12",
        all_results=all_results,
        results_route_list=RESULT_ROWS,
        kpi_mapping=KPI_MAPPING,
        route_type=route_type,
    )
    res = all_results[0]
    pprint(res)
    assert res["route_id"] == "A12"
    assert res["t1_DG_org"] == 100.0
    assert res["t1_DG_best"] == 120.0
    assert res["t1_seg_outliers"] == 2
    assert res["t2_DG_best"] == 140.0
    assert res["t2_seg_outliers"] == 1
    assert res["t2_solver"] == "lkh"
    assert any(k["key"] == "t1_DG_best" for k in kpis)
    assert any(k["key"] == "t2_DG_best" for k in kpis)

def test_generate_type1_only():
    """Test extraction with route_type = 'type1'."""
    all_results = []
    all_results, kpis = generate_result_dict(
        route_id="A12",
        all_results=all_results,
        results_route_list=RESULT_ROWS,
        kpi_mapping=KPI_MAPPING,
        route_type="type1",
    )
    res = all_results[0]
    assert "t1_DG_best" in res
    assert "t2_DG_best" not in res
    assert all(k["key"].startswith("t1_") or k["key"] == "route_id" for k in kpis)

def test_generate_type2_only():
    """Test extraction with route_type = 'type2'."""
    all_results = []
    all_results, kpis = generate_result_dict(
        route_id="A12",
        all_results=all_results,
        results_route_list=RESULT_ROWS,
        kpi_mapping=KPI_MAPPING,
        route_type="type2",
    )
    res = all_results[0]
    assert "t2_DG_best" in res
    assert "t1_DG_best" not in res
    assert all(k["key"].startswith("t2_") or k["key"] == "route_id" for k in kpis)

def test_missing_required_field_raises():
    """If a mapping entry is missing a required key → raise ValueError."""
    bad_mapping = [
        {"name": "Bad", "key": "x", "type": "both"}  # missing 'val'
    ]
    with pytest.raises(ValueError):
        generate_result_dict(
            route_id="A12",
            all_results=[],
            results_route_list=RESULT_ROWS,
            kpi_mapping=bad_mapping,
            route_type="both",
        )

def test_invalid_type_raises():
    """If mapping type is not 'type1', 'type2', or 'both' → error."""
    bad_mapping = [
        {"name": "Bad", "key": "x", "type": "xxx", "val": lambda r: 1}
    ]
    with pytest.raises(ValueError):
        generate_result_dict(
            route_id="A12",
            all_results=[],
            results_route_list=RESULT_ROWS,
            kpi_mapping=bad_mapping,
            route_type="both",
        )

def test_val_not_callable_raises():
    """If val is not callable → error."""
    bad_mapping = [
        {"name": "Bad", "key": "x", "type": "type1", "val": 12345}
    ]
    with pytest.raises(ValueError):
        generate_result_dict(
            route_id="A12",
            all_results=[],
            results_route_list=RESULT_ROWS,
            kpi_mapping=bad_mapping,
            route_type="both",
        )

def test_row_missing_fields_returns_none_not_error():
    """If lambda fails because field missing, return None gracefully."""
    bad_rows = [
        {"strict_order": True, "route_id": "A12"},  # Missing DG_best, etc.
    ]
    all_results = []
    all_results, kpis = generate_result_dict(
        route_id="A12",
        all_results=all_results,
        results_route_list=bad_rows,
        kpi_mapping=KPI_MAPPING,
        route_type="both",
    )
    res = all_results[0]
    assert res["route_id"] == "A12"
    assert res["t1_DG_org"] is None
    assert res["t2_DG_best"] is None

if __name__ == "__main__":
    test_generate_both_types_ok()
    test_generate_type1_only()
    test_generate_type2_only()
    test_missing_required_field_raises()
    test_invalid_type_raises()
    test_val_not_callable_raises()
    test_row_missing_fields_returns_none_not_error()
