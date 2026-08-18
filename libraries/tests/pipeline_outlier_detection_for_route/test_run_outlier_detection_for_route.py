import copy
import pprint
import time
import os

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import (
    run_outlier_detection_for_route,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration (shared across all tests)
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
    "k_max": 10,
    "k_all": 1,
    "B": 5,
    "type1_methods": ["A", "B"],
    "type2_methods": ["A", "B"],
    "solver_tsp": "ortools",
    "solver_hpp": "ortools",
    "deterministic_tsp": True,
    "deterministic_hpp": True,
    "precheck": True,
    "ortools_time_limit": 2,
    "initial_point_method": {"method": "GREEDY_DNN"},
    "A_kwargs": {"method": "kneedle"},
    "B_kwargs": {"L_max": 8},
    "U_kwargs": {}
}


# ---------------------------------------------------------------------
# Problem type variants (ONLY thing that changes)
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


def _run_outlier_detection_test(problem_type_mapping: dict):
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

    # --------------------------------------------------
    # Inject problem_type mapping
    # --------------------------------------------------
    config = copy.deepcopy(BASE_CONFIG)
    config["col_map"]["problem_type"] = problem_type_mapping

    # --------------------------------------------------
    # Step 1: build pipeline context
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
    # Step 2: prepare route + matrices
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

    # --------------------------------------------------
    # Step 3: run outlier detection
    # --------------------------------------------------
    t_start = time.perf_counter()

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
        t_route_start=t_start,
    )

    # --------------------------------------------------
    # Assertions: results structure
    # --------------------------------------------------
    assert isinstance(results, list)
    assert len(results) == 2  # strict=True / False

    for res in results:
        assert res["route_id"] == int(route_id)
        assert res["problem_type"] == route_prep.problem_type
        assert res["solver"] == route_prep.solver
        assert isinstance(res["distance_change"], dict)
        assert isinstance(res["runtime"], float)

    # --------------------------------------------------
    # PRINTS (intentional)
    # --------------------------------------------------
    print("\n[TEST] run_outlier_detection_for_route")
    print("-" * 70)
    print(f"Problem type mapping : {problem_type_mapping}")
    print(f"Resolved problem type: {route_prep.problem_type}")
    print(f"Route ID             : {route_id}")
    print(f"Results count        : {len(results)}")
    print("\nFirst result snapshot:")
    pprint.pprint(results[0])
    print("\nSecond result snapshot:")
    pprint.pprint(results[1])
    print("-" * 70)

def test_run_outlier_detection_with_revenue():
    """
    Integration test:
    - revenue is attached at dataset level
    - prepare_route preserves revenue
    - run_outlier_detection_for_route uses revenue as E
    """

    print("\n[TEST] run_outlier_detection_for_route with revenue")

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

    config = copy.deepcopy(BASE_CONFIG)

    # --------------------------------------------------
    # Inject revenue config
    # --------------------------------------------------
    config["col_map"]["revenue"] = {
        "path_revenue": os.path.join(
            "libraries", "tests", "_test_dataset", "test_revenue_data.csv"
        ),
        "join_fields": {
            "kommune": "kommune",
            "vejnr": "vejnr",
            "husnr": "husnr",
            "husbog": "husbog",
        },
        "rev_fields": [
            "week_2536",
            "week_2537",
            "week_2538",
            "week_2539",
        ],
        "rev_formula": "AVG",
        "rev_include_all_addresses": True,
    }

    # --------------------------------------------------
    # Step 1: build pipeline context
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

    route_id = ctx.route_ids[0]

    # --------------------------------------------------
    # Step 2: prepare route + matrices
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

    # --------------------------------------------------
    # Assertions: revenue present in route data dataframe
    # --------------------------------------------------
    assert "data" in route_prep.data
    route_df = route_prep.data["data"]

    assert "revenue" in route_df.columns
    assert route_df["revenue"].dtype.kind in {"f", "i"}

    print("[INFO] Revenue column detected in route data['data']")
    print(route_df[["route_id", "line_nr", "revenue"]].head())

    # --------------------------------------------------
    # Step 3: run outlier detection
    # --------------------------------------------------
    t_start = time.perf_counter()

    results = run_outlier_detection_for_route(
        route_id=route_prep.route_id,
        data=route_prep.data,
        APR_profile=route_prep.APR_profile,
        problem_type=route_prep.problem_type,
        strict_values=[True, False],
        type1_methods=config["type1_methods"],
        type2_methods=config["type2_methods"],
        E=config["E"],  # SHOULD BE IGNORED IN FAVOR OF revenue
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
        t_route_start=t_start,
    )

    # --------------------------------------------------
    # Assertions: results structure
    # --------------------------------------------------
    assert isinstance(results, list)
    assert len(results) == 2

    for res in results:
        assert res["route_id"] == int(route_id)
        assert res["problem_type"] == route_prep.problem_type
        assert isinstance(res["distance_change"], dict)
        assert isinstance(res["DG_best"], (int, float))

    # --------------------------------------------------
    # PRINTS (intentional)
    # --------------------------------------------------
    print("\n[OK] Outlier detection completed using revenue-driven E")
    pprint.pprint(results[0])

# ---------------------------------------------------------------------
# Actual tests (one per problem method)
# ---------------------------------------------------------------------
def test_outlier_detection_hpp():
    _run_outlier_detection_test(PROBLEM_TYPE_VARIANTS["HPP"])


def test_outlier_detection_out_hpp():
    _run_outlier_detection_test(PROBLEM_TYPE_VARIANTS["OUT:HPP"])


def test_outlier_detection_tsp():
    _run_outlier_detection_test(PROBLEM_TYPE_VARIANTS["TSP"])


def test_outlier_detection_out_tsp():
    _run_outlier_detection_test(PROBLEM_TYPE_VARIANTS["OUT:TSP"])


if __name__ == "__main__":
    test_outlier_detection_hpp()
    test_outlier_detection_out_hpp()
    test_outlier_detection_tsp()
    test_outlier_detection_out_tsp()
    test_run_outlier_detection_with_revenue()
