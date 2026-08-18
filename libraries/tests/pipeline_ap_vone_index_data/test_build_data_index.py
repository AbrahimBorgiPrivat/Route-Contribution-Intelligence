import copy
import os
import tempfile
import time

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import init_pipeline_context
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import prepare_route_and_matrices
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import run_outlier_detection_for_route
from libraries.utils.pipelines.d_application_layer.application.V1.pipeline_ap_vone_route_data import build_single_route_data
from libraries.utils.pipelines.d_application_layer.application.V1.pipeline_ap_vone_index_data import build_data_index
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Runtime-like configuration (single source of truth)
# ---------------------------------------------------------------------
BASE_CONFIG = {
    "dataset": "libraries/tests/_test_dataset/test_data.csv",
    "routing": {
        "route_type": "both",
        "start_routes": 0,
        "max_routes": 2,
    },
    "algorithm": {
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
        "U_kwargs": {},
    },

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
        "problem_type": {
            "name": "beregning",
            "OUT:TSP": [0, 1, 2],
        },
    },
}

def test_build_data_index_from_config():
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
    print("[TEST] build_data_index (config-driven)")
    print("=" * 80)

    cfg = copy.deepcopy(BASE_CONFIG)
    # --------------------------------------------------
    # Step 1: dataset context (config-driven)
    # --------------------------------------------------
    ctx = init_pipeline_context(
        file_path=cfg["dataset"],
        col_map=cfg["col_map"],
        route_type=cfg["routing"]["route_type"],
        A_kwargs=cfg["algorithm"]["A_kwargs"],
        B_kwargs=cfg["algorithm"]["B_kwargs"],
        U_kwargs=cfg["algorithm"]["U_kwargs"],
        APR=cfg["algorithm"]["APR"],
        start_routes=cfg["routing"]["start_routes"],
        max_routes=cfg["routing"]["max_routes"],
    )
    assert len(ctx.route_ids) == cfg["routing"]["max_routes"]
    print(f"[INFO] Using route_ids={ctx.route_ids}")
    route_outputs = []

    # --------------------------------------------------
    # Step 2: per-route data generation
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir = tmpdir
        for route_id in ctx.route_ids:
            route_prep = prepare_route_and_matrices(
                route_id=route_id,
                df=ctx.df,
                APR=ctx.APR,
                solver_tsp=cfg["algorithm"]["solver_tsp"],
                solver_hpp=cfg["algorithm"]["solver_hpp"],
                deterministic_tsp=cfg["algorithm"]["deterministic_tsp"],
                deterministic_hpp=cfg["algorithm"]["deterministic_hpp"],
                chunk_size_osrm=50,
                chunk_size_osm=2,
                use_rotated_side=True,
            )
            results = run_outlier_detection_for_route(
                route_id=route_prep.route_id,
                data=route_prep.data,
                APR_profile=route_prep.APR_profile,
                problem_type=route_prep.problem_type,
                strict_values=ctx.strict_values,
                type1_methods=cfg["algorithm"]["type1_methods"],
                type2_methods=cfg["algorithm"]["type2_methods"],
                E=cfg["algorithm"]["E"],
                z=cfg["algorithm"]["z"],
                k_max=cfg["algorithm"]["k_max"],
                k_all=cfg["algorithm"]["k_all"],
                B=cfg["algorithm"]["B"],
                L_u=route_prep.L_u,
                deterministic=route_prep.deterministic,
                precheck=cfg["algorithm"]["precheck"],
                solver=route_prep.solver,
                ortools_time_limit=cfg["algorithm"]["ortools_time_limit"],
                initial_point_method=cfg["algorithm"]["initial_point_method"],
                A_kwargs=cfg["algorithm"]["A_kwargs"],
                B_kwargs=cfg["algorithm"]["B_kwargs"],
                U_kwargs=cfg["algorithm"]["U_kwargs"],
                t_route_start=time.perf_counter(),
            )
            output = build_single_route_data(
                route_id=str(route_id),
                route_data=route_prep.data,
                results_route_list=results,
                save_dir=save_dir,
                E=cfg["algorithm"]["E"],
                problem_type=route_prep.problem_type,
            )
            route_outputs.append(output)
        assert len(route_outputs) == cfg["routing"]["max_routes"]

        # --------------------------------------------------
        # Step 3: build index (UNDER TEST)
        # --------------------------------------------------
        index_path = build_data_index(
            save_dir=save_dir,
            kpi_mapping=[],
            route_outputs=route_outputs,
            use_data=True,
            index_filename="routes_index.json",
        )

        # --------------------------------------------------
        # Assertions
        # --------------------------------------------------
        assert os.path.isfile(index_path)
        print(f"[OK] routes_index.json written at: {index_path}")
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()
        for route_id in ctx.route_ids:
            assert str(route_id) in index_content
        print("\n[Index JSON preview]")
        print(index_content[:400])

if __name__ == "__main__":
    test_build_data_index_from_config()
