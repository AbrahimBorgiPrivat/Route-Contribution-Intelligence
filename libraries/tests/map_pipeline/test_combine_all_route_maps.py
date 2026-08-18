import copy
import os
import tempfile
from pathlib import Path

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import (
    run_outlier_detection_for_route,
)
from libraries.utils.visualization.map_pipeline import (
    build_route_map,
    combine_all_route_maps,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration (same pattern as other visualization tests)
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
        "problem_type": {
            "name": "beregning",
            "TSP": [0, 1, 2],
        },
    },
    "route_type": "both",
    "APR": 0.03,
    "start_routes": None,
    "max_routes": None,
    # algorithm params
    "E": 5.0,
    "z": 0.0,
    "k_max": 5,
    "k_all": 1,
    "B": 3,
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


def test_combine_all_route_maps():
    # --------------------------------------------------
    # Skip if OSRM services are unavailable
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

    assert len(ctx.route_ids) >= 2, "Need at least two routes to test combination"

    route_ids = ctx.route_ids[:2]

    route_maps = []

    # --------------------------------------------------
    # Step 2: build maps for two routes
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        views_root = Path(tmpdir)

        for route_id in route_ids:
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

            map_info = build_route_map(
                route_id=str(route_id),
                route_data=route_prep.data,
                results_list=results,
                views_root=str(views_root),
                saved_or_show="save",
            )

            route_maps.append(map_info)

        # --------------------------------------------------
        # Step 3: combine maps (UNDER TEST)
        # --------------------------------------------------
        output_path = combine_all_route_maps(
            route_maps=route_maps,
            views_root=str(views_root),
        )

        # --------------------------------------------------
        # Assertions
        # --------------------------------------------------
        assert isinstance(output_path, Path)
        assert output_path.exists()
        assert output_path.name == "all_routes_map.html"

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] combine_all_route_maps")
        print("-" * 70)
        print(f"Combined map path: {output_path}")
        print(f"Routes combined  : {route_ids}")
        print("-" * 70)


def test_combine_all_route_maps_empty_input():
    """
    Explicit contract test: empty input must raise.
    """
    try:
        combine_all_route_maps([])
    except ValueError as e:
        assert "No route maps to combine" in str(e)
    else:
        raise AssertionError("Expected ValueError for empty route_maps input")

if __name__ == "__main__":
    test_combine_all_route_maps()
    test_combine_all_route_maps_empty_input()
    