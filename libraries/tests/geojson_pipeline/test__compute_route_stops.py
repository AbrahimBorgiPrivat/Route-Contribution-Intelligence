import copy
import time

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import (
    run_outlier_detection_for_route,
)
from libraries.utils.visualization.geojson_pipeline import (
    _compute_route_stops,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration (shared)
# ---------------------------------------------------------------------
BASE_CONFIG = {
    "dataset": "libraries/tests/_test_dataset/test_data.csv",
    "col_map": {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "address": {
            "fields": ["adresse"],
            "separator": "; ",
        },
        "transform": {
            "convert_from": "EPSG:25832",
            "convert_to": "EPSG:4326",
        },
        "type": {
            "name": "beregning",
            "foot": {"val": 0, "annotations": "distance"},
            "car": {"val": 1, "annotations": "duration"},
            "cycle": {"val": 2, "annotations": "distance"},
        },
    },
    "route_type": "both",
    "APR": 0.03,
    "E": 5.0,
    "solver_tsp": "ortools",
    "solver_hpp": "ortools",
    "deterministic_tsp": True,
    "deterministic_hpp": True,
    "type1_methods": ["A", "B"],
    "type2_methods": ["A", "B"],
    "z": 0.0,
    "k_max": 5,
    "k_all": 1,
    "B": 5,
    "precheck": True,
    "ortools_time_limit": 2,
    "initial_point_method": {"method": "GREEDY_DNN"},
    "A_kwargs": {"method": "kneedle"},
    "B_kwargs": {"L_max": 8},
    "U_kwargs": {}
}


# ---------------------------------------------------------------------
# Problem type variants
# ---------------------------------------------------------------------
PROBLEM_TYPE_VARIANTS = {
    "TSP": {
        "name": "beregning",
        "TSP": [0, 1, 2],
    },
    "HPP": {
        "name": "beregning",
        "HPP": [0, 1, 2],
    },
    "OUT:TSP": {
        "name": "beregning",
        "OUT:TSP": [0, 1, 2],
    },
    "OUT:HPP": {
        "name": "beregning",
        "OUT:HPP": [0, 1, 2],
    },
}


def _run_compute_route_stops_test(problem_type_mapping: dict):
    # --------------------------------------------------
    # Skip if OSRM not available
    # --------------------------------------------------
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )

    print("\n" + "=" * 80)
    print(f"[TEST] _compute_route_stops for problem_type mapping: {problem_type_mapping}")
    print("=" * 80)

    config = copy.deepcopy(BASE_CONFIG)
    config["col_map"]["problem_type"] = problem_type_mapping

    # --------------------------------------------------
    # Step 1: dataset context
    # --------------------------------------------------
    ctx = init_pipeline_context(
        file_path=config["dataset"],
        col_map=config["col_map"],
        route_type=config["route_type"],
        A_kwargs=config["A_kwargs"],
        B_kwargs=config["B_kwargs"],
        U_kwargs=config["U_kwargs"],
        APR=config["APR"],
        start_routes=None,
        max_routes=None,
    )

    route_id = ctx.route_ids[0]
    print(f"[INFO] Using route_id={route_id}")

    # --------------------------------------------------
    # Step 2: route preparation
    # --------------------------------------------------
    route_prep = prepare_route_and_matrices(
        route_id=route_id,
        df=ctx.df,
        APR=ctx.APR,
        solver_tsp=config["solver_tsp"],
        solver_hpp=config["solver_hpp"],
        deterministic_tsp=config["deterministic_tsp"],
        deterministic_hpp=config["deterministic_hpp"],
        chunk_size_osrm=50,
        chunk_size_osm=2,
        use_rotated_side=True,
    )

    print(f"[INFO] problem_type resolved as: {route_prep.problem_type}")

    # --------------------------------------------------
    # Step 3: outlier detection
    # --------------------------------------------------
    results = run_outlier_detection_for_route(
        route_id=route_prep.route_id,
        data=route_prep.data,
        APR_profile=route_prep.APR_profile,
        problem_type=route_prep.problem_type,
        strict_values=[True, False],
        type1_methods=config["type1_methods"],
        type2_methods=config["type2_methods"],
        E=config["E"],
        z=config["z"],
        k_max=config["k_max"],
        k_all=config["k_all"],
        B=config["B"],
        L_u=route_prep.L_u,
        deterministic=route_prep.deterministic,
        precheck=config["precheck"],
        solver=route_prep.solver,
        ortools_time_limit=config["ortools_time_limit"],
        initial_point_method=config["initial_point_method"],
        A_kwargs=config["A_kwargs"],
        B_kwargs=config["B_kwargs"],
        U_kwargs=config["U_kwargs"],
        t_route_start=time.perf_counter(),
    )

    sol = results[0]

    # --------------------------------------------------
    # Step 4: compute route stops (UNDER TEST)
    # --------------------------------------------------
    stops = _compute_route_stops(
        route_id=str(route_id),
        R=sol["R_original"],
        significant=set(sol["S_outlier"]),
        route_data=route_prep.data,
        E=config["E"],
        APR=sol["APR"],
        problem_type=route_prep.problem_type,
    )

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------
    assert isinstance(stops, list)
    assert len(stops) == len(sol["R_original"])
    
    for i, stop in enumerate(stops):
        assert stop["route_id"] == str(route_id)
        assert stop["sequence_index"] == i
        assert isinstance(stop["route_number"], int)
        assert "revenue" in stop
        assert "distance_to_next" in stop
        assert "apr_cost" in stop

    print(f"[OK] Computed {len(stops)} stops")

    for stop in stops:
        print(
            f"  stop seq={stop['sequence_index']} "
            f"node={stop['route_number']} "
            f"dist_next={stop['distance_to_next']} "
            f"apr_cost={stop['apr_cost']}"
        )

    if route_prep.problem_type in {"HPP", "OUT:HPP"}:
        assert stops[-1]["distance_to_next"] is None
        print("[OK] Last stop has no distance_to_next (HPP behavior)")
    else:
        assert stops[-1]["distance_to_next"] is not None
        print("[OK] Last stop has distance_to_next (TSP behavior)")


# ---------------------------------------------------------------------
# Actual tests
# ---------------------------------------------------------------------
def test_compute_route_stops_tsp():
    _run_compute_route_stops_test(PROBLEM_TYPE_VARIANTS["TSP"])


def test_compute_route_stops_hpp():
    _run_compute_route_stops_test(PROBLEM_TYPE_VARIANTS["HPP"])


def test_compute_route_stops_out_tsp():
    _run_compute_route_stops_test(PROBLEM_TYPE_VARIANTS["OUT:TSP"])


def test_compute_route_stops_out_hpp():
    _run_compute_route_stops_test(PROBLEM_TYPE_VARIANTS["OUT:HPP"])


if __name__ == "__main__":
    test_compute_route_stops_tsp()
    test_compute_route_stops_hpp()
    test_compute_route_stops_out_tsp()
    test_compute_route_stops_out_hpp()
