import copy
import time
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
from libraries.utils.pipelines.d_application_layer.static.V1.pipeline_st_vone_route_presentation import (
    present_single_route_static,
)
from libraries.utils.pipelines.d_application_layer.static.V1.pipeline_st_vone_index_presentation import (
    present_static_index,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration (same pattern as other pipeline tests)
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
    "E": 5.0,
    "z": 0.0,
    "k_max": 8,
    "k_all": 1,
    "B": 4,
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

TEMPLATE_ROOT = "libraries/tests/_test_templates/templates"


def test_present_static_index():
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

    assert len(ctx.route_ids) >= 2, "Need at least two routes to render index page"

    route_ids = ctx.route_ids[:2]

    # --------------------------------------------------
    # Step 2: build per-route static presentation
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        views_root = Path(tmpdir)

        all_maps = []
        all_results = []
        kpis = []

        for route_id in route_ids:
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

            all_maps, all_results, kpis = present_single_route_static(
                route_id=route_id,
                data=route_prep.data,
                results_route_list=results,
                views_root=str(views_root),
                template_root=TEMPLATE_ROOT,
                all_maps=all_maps,
                all_results=all_results,
                kpi_mapping=[],
                route_type=config["route_type"],
                html_render=True,
            )

        assert len(all_maps) == 2
        assert len(all_results) == 2

        # --------------------------------------------------
        # Step 3: index presentation (UNDER TEST)
        # --------------------------------------------------
        present_static_index(
            all_maps=all_maps,
            all_results=all_results,
            kpis=kpis,
            views_root=str(views_root),
            html_render=True,
            template_root=TEMPLATE_ROOT,
        )

        # --------------------------------------------------
        # Assertions: filesystem side effects
        # --------------------------------------------------
        maps_dir = views_root / "maps"
        index_html = views_root / "index.html"

        assert maps_dir.exists()
        assert (maps_dir / "all_routes_map.html").exists()
        assert index_html.exists()

        html = index_html.read_text(encoding="utf-8")

        # Basic sanity checks
        for route_id in route_ids:
            assert str(route_id) in html

        assert "./maps/all_routes_map.html" in html

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] present_static_index")
        print("-" * 70)
        print(f"Routes indexed     : {route_ids}")
        print(f"Combined map exists: {maps_dir / 'all_routes_map.html'}")
        print(f"Index page         : {index_html}")
        print("-" * 70)


if __name__ == "__main__":
    test_present_static_index()
