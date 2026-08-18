import copy
import pprint
import time
import os
import tempfile
import json
from pathlib import Path

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)
from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_outlier_detection_for_route_v2 import (
    run_outlier_detection_for_route_v2,
)
from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _get_cache_file_path,
)
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
        "address": {"fields": ["adresse"], "separator": "; "},
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


# ---------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------
def _run_outlier_detection_v2_test(
    *,
    label: str,
    problem_type_mapping: dict,
    c_cache_config,
    with_revenue: bool = False,
):
    print("\n" + "=" * 80)
    print(f"[V2 TEST] {label}")
    print("=" * 80)

    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )

    config = copy.deepcopy(BASE_CONFIG)
    config["col_map"]["problem_type"] = problem_type_mapping

    if with_revenue:
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

    t_start = time.perf_counter()

    results = run_outlier_detection_for_route_v2(
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
        c_cache_config=c_cache_config,
    )

    assert isinstance(results, list)
    assert len(results) == 2

    pprint.pprint(results[0])

    # ------------------------------------------------------------
    # Print cached files
    # ------------------------------------------------------------
    if c_cache_config and c_cache_config.get("enabled", False):

        path_type1 = _get_cache_file_path(
            base_path=c_cache_config["base_path"],
            label=c_cache_config["label"],
            route_id=route_id,
            strict=True,
        )
        path_type2 = _get_cache_file_path(
            base_path=c_cache_config["base_path"],
            label=c_cache_config["label"],
            route_id=route_id,
            strict=False,
        )

        print("\nCache Type1 Path:", path_type1)
        print("Cache Type2 Path:", path_type2)

        if path_type1.exists():
            print("\n--- Type1 Cache Content ---")
            with open(path_type1, "r") as f:
                pprint.pprint(json.load(f))

        if path_type2.exists():
            print("\n--- Type2 Cache Content ---")
            with open(path_type2, "r") as f:
                pprint.pprint(json.load(f))

    print("=" * 80)


# ---------------------------------------------------------------------
# TEST SUITE
# ---------------------------------------------------------------------
def test_v2_hpp_cache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_cfg = {"enabled": True, "base_path": tmp_dir, "label": "v2_hpp"}
        _run_outlier_detection_v2_test(
            label="HPP first run",
            problem_type_mapping=PROBLEM_TYPE_VARIANTS["HPP"],
            c_cache_config=cache_cfg,
        )
        _run_outlier_detection_v2_test(
            label="HPP second run (reuse)",
            problem_type_mapping=PROBLEM_TYPE_VARIANTS["HPP"],
            c_cache_config=cache_cfg,
        )


def test_v2_out_hpp_cache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_cfg = {"enabled": True, "base_path": tmp_dir, "label": "v2_out_hpp"}
        _run_outlier_detection_v2_test(
            label="OUT:HPP first run",
            problem_type_mapping=PROBLEM_TYPE_VARIANTS["OUT:HPP"],
            c_cache_config=cache_cfg,
        )


def test_v2_tsp_no_cache():
    _run_outlier_detection_v2_test(
        label="TSP no cache",
        problem_type_mapping=PROBLEM_TYPE_VARIANTS["TSP"],
        c_cache_config=None,
    )


def test_v2_with_revenue():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_cfg = {"enabled": True, "base_path": tmp_dir, "label": "v2_revenue"}
        _run_outlier_detection_v2_test(
            label="OUT:TSP revenue + cache",
            problem_type_mapping=PROBLEM_TYPE_VARIANTS["OUT:TSP"],
            c_cache_config=cache_cfg,
            with_revenue=True,
        )


if __name__ == "__main__":
    test_v2_hpp_cache()
    test_v2_out_hpp_cache()
    test_v2_tsp_no_cache()
    test_v2_with_revenue()
