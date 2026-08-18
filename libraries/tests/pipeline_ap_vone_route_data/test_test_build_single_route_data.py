import copy
import os
import tempfile
import time

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import init_pipeline_context
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import prepare_route_and_matrices
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import run_outlier_detection_for_route
from libraries.utils.pipelines.d_application_layer.application.V1.pipeline_ap_vone_route_data import build_single_route_data
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration
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
# Problem type variants we want to lock down
# ---------------------------------------------------------------------
PROBLEM_TYPE_VARIANTS = {
    "TSP": {
        "name": "beregning",
        "TSP": [0, 1, 2],
    },
    "OUT:HPP": {
        "name": "beregning",
        "OUT:HPP": [0, 1, 2],
    },
}


def _run_build_single_route_data_test(problem_type_mapping: dict):
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
    print(f"[TEST] build_single_route_data for problem_type={problem_type_mapping}")
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
        strict_values=ctx.strict_values,
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

    # --------------------------------------------------
    # Step 4: build single-route data (UNDER TEST)
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        output = build_single_route_data(
            route_id=str(route_id),
            route_data=route_prep.data,
            results_route_list=results,
            save_dir=tmpdir,
            E=config["E"],
            problem_type=route_prep.problem_type,
        )

        assert output["route_id"] == str(route_id)

        for key in ("index", "markers", "routes"):
            assert key in output
            assert os.path.isfile(output[key])

        print("[OK] Generated files:")
        for k, v in output.items():
            print(f"  {k}: {v}")

        with open(output["index"], "r", encoding="utf-8") as f:
            index_json = f.read()

        assert "stops_original" in index_json
        assert "stops_optimal" in index_json

        print("\n[Index JSON preview]")
        print(index_json[:400])

def test_build_single_route_data_with_revenue():
    """
    Integration test:
    - revenue is attached at dataset level
    - prepare_route preserves revenue
    - build_single_route_data uses revenue-driven E
    """

    print("\n" + "=" * 80)
    print("[TEST] build_single_route_data with revenue")
    print("=" * 80)

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

    # --------------------------------------------------
    # Assertions: revenue present
    # --------------------------------------------------
    assert "revenue" in route_prep.data['data'].columns
    assert route_prep.data['data']["revenue"].dtype.kind in {"f", "i"}

    print("[INFO] Revenue column detected in route data")
    print(route_prep.data['data'][["route_id", "line_nr", "revenue"]].head())

    # --------------------------------------------------
    # Step 3: outlier detection
    # --------------------------------------------------
    results = run_outlier_detection_for_route(
        route_id=route_prep.route_id,
        data=route_prep.data,
        APR_profile=route_prep.APR_profile,
        problem_type=route_prep.problem_type,
        strict_values=ctx.strict_values,
        type1_methods=config["type1_methods"],
        type2_methods=config["type2_methods"],
        E=config["E"],  # should be overridden by revenue
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

    # --------------------------------------------------
    # Step 4: build single-route data (UNDER TEST)
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        output = build_single_route_data(
            route_id=str(route_id),
            route_data=route_prep.data,
            results_route_list=results,
            save_dir=tmpdir,
            E=config["E"],  # overridden internally
            problem_type=route_prep.problem_type,
        )

        assert output["route_id"] == str(route_id)

        for key in ("index", "markers", "routes"):
            assert key in output
            assert os.path.isfile(output[key])

        with open(output["index"], "r", encoding="utf-8") as f:
            index_json = f.read()

        assert "stops_original" in index_json
        assert "stops_optimal" in index_json

        print("[OK] build_single_route_data completed using revenue-driven E")
        print("\n[Index JSON preview]")
        print(index_json[:400])

# ---------------------------------------------------------------------
# Actual tests
# ---------------------------------------------------------------------
def test_build_single_route_data_tsp():
    _run_build_single_route_data_test(PROBLEM_TYPE_VARIANTS["TSP"])

def test_build_single_route_data_out_hpp():
    _run_build_single_route_data_test(PROBLEM_TYPE_VARIANTS["OUT:HPP"])

if __name__ == "__main__":
    test_build_single_route_data_tsp()
    test_build_single_route_data_out_hpp()
    test_build_single_route_data_with_revenue()
