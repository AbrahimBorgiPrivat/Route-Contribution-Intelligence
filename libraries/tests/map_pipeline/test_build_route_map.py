import copy
import os
import tempfile

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import (
    run_outlier_detection_for_route,
)
from libraries.utils.visualization.map_pipeline import build_route_map
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
    "start_routes": None,
    "max_routes": None,
    "E": 5.0,
    "z": 0.0,
    "k_max": 8,
    "k_all": 1,
    "B": 5,
    "type1_methods": ["A"],
    "type2_methods": ["A"],
    "solver_tsp": "ortools",
    "solver_hpp": "ortools",
    "deterministic_tsp": True,
    "deterministic_hpp": True,
    "precheck": True,
    "ortools_time_limit": 2,
    "initial_point_method": {"method": "GREEDY_DNN"},
    "A_kwargs": {"method": "kneedle"},
    "B_kwargs": {"L_max": 8},
    "U_kwargs": {},
}


# ---------------------------------------------------------------------
# Problem type variants
# ---------------------------------------------------------------------
PROBLEM_TYPE_VARIANTS = {
    "HPP": {
        "name": "beregning",
        "HPP": [0, 1, 2],
    },
    "OUT:HPP": {
        "name": "beregning",
        "OUT:HPP": [0, 1, 2],
    },
    "TSP": {
        "name": "beregning",
        "TSP": [0, 1, 2],
    },
    "OUT:TSP": {
        "name": "beregning",
        "OUT:TSP": [0, 1, 2],
    },
}


def _run_build_route_map_test(problem_type_mapping: dict):
    # --------------------------------------------------
    # Skip if OSRM not running
    # --------------------------------------------------
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM service not running",
    )

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
        start_routes=config["start_routes"],
        max_routes=config["max_routes"],
    )
    assert ctx.route_ids
    route_id = ctx.route_ids[0]

    # --------------------------------------------------
    # Step 2: prepare route
    # --------------------------------------------------
    route_prep = prepare_route_and_matrices(
        route_id=route_id,
        df=ctx.df,
        APR=ctx.APR,
        solver_tsp=config["solver_tsp"],
        solver_hpp=config["solver_hpp"],
        deterministic_tsp=config["deterministic_tsp"],
        deterministic_hpp=config["deterministic_hpp"],
        chunk_size_osrm=25,
        chunk_size_osm=2,
        use_rotated_side=True,
    )

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
        t_route_start=0.0,
    )

    assert results

    # --------------------------------------------------
    # Step 4: build map (under test)
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        out = build_route_map(
            route_id=str(route_id),
            route_data=route_prep.data,
            results_list=results,
            views_root=tmpdir,
            saved_or_show="save",
        )

        # --------------------------------------------------
        # Assertions: contract
        # --------------------------------------------------
        assert isinstance(out, dict)
        assert "map_file" in out
        assert "plotter" in out

        map_file = out["map_file"]
        assert isinstance(map_file, str)

        abs_map_path = os.path.join(tmpdir, map_file)
        assert os.path.exists(abs_map_path)

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] build_route_map")
        print("-" * 70)
        print(f"Problem type mapping : {problem_type_mapping}")
        print(f"Resolved problem type: {route_prep.problem_type}")
        print(f"Route ID             : {route_id}")
        print(f"Map file             : {abs_map_path}")
        print("Result layers:")
        for r in results:
            print(f"  - strict={r['strict_order']} | problem_type={r['problem_type']}")
        print("-" * 70)


# ---------------------------------------------------------------------
# Actual tests
# ---------------------------------------------------------------------
def test_build_route_map_hpp():
    _run_build_route_map_test(PROBLEM_TYPE_VARIANTS["HPP"])


def test_build_route_map_out_hpp():
    _run_build_route_map_test(PROBLEM_TYPE_VARIANTS["OUT:HPP"])


def test_build_route_map_tsp():
    _run_build_route_map_test(PROBLEM_TYPE_VARIANTS["TSP"])


def test_build_route_map_out_tsp():
    _run_build_route_map_test(PROBLEM_TYPE_VARIANTS["OUT:TSP"])


if __name__ == "__main__":
    test_build_route_map_hpp()
    test_build_route_map_out_hpp()
    test_build_route_map_tsp()
    test_build_route_map_out_tsp()
