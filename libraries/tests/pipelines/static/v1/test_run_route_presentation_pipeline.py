import tempfile
from pathlib import Path

from libraries.utils.pipelines.pipelines.static.v1.run_route_presentation_pipeline import run_route_presentation_pipeline
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


def test_run_route_presentation_pipeline_static_v1():
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

    with tempfile.TemporaryDirectory() as tmpdir:
        views_root = Path(tmpdir) / "static_v1"

        # --------------------------------------------------
        # Run pipeline (UNDER TEST)
        # --------------------------------------------------
        all_results_route_list, all_maps = run_route_presentation_pipeline(
            file_path="libraries/tests/_test_dataset/test_data.csv",
            views_root=str(views_root),
            template_root="libraries/tests/_test_templates/templates",
            html_render=True,
            E=5.0,
            APR=0.03,
            z=0.0,
            k_max=8,
            k_all=1,
            B=4,
            solver_tsp="ortools",
            solver_hpp="ortools",
            deterministic_tsp=True,
            deterministic_hpp=True,
            precheck=True,
            ortools_time_limit=2,
            initial_point_method={"method": "GREEDY_DNN"},
            A_kwargs={"method": "kneedle"},
            B_kwargs={"L_max": 8},
            U_kwargs={},
            type1_methods=["A", "B"],
            type2_methods=["A", "B"],
            chunk_size_osm=2,
            chunk_size_osrm=25,
            use_rotated_side=True,
            offset_m=4.5,
            entry_angle_deg=60.0,
            exit_angle_deg=60.0,
            route_type="both",
            start_routes=0,
            max_routes=2,
            col_map={
                "route_id": {"name": "id"},
                "lon": {"name": "vejx"},
                "lat": {"name": "vejy"},
                "line_nr": {"name": "linienr"},
                "transform": {
                    "convert_from": "EPSG:25832",
                    "convert_to": "EPSG:4326",
                },
                "problem_type": {
                    "name": "beregning",
                    "OUT:TSP": [0, 1, 2],
                },
            },
            kpi_mapping=[],
        )

        # --------------------------------------------------
        # Assertions: return values
        # --------------------------------------------------
        assert isinstance(all_results_route_list, list)
        assert isinstance(all_maps, list)
        assert len(all_results_route_list) > 0
        assert len(all_maps) == 2

        # --------------------------------------------------
        # Assertions: filesystem outputs
        # --------------------------------------------------
        maps_dir = views_root / "maps"
        routes_dir = views_root / "routes"
        index_html = views_root / "index.html"

        assert maps_dir.exists()
        assert routes_dir.exists()
        assert index_html.exists()

        map_files = list(maps_dir.glob("route_*_map.html"))
        route_pages = list(routes_dir.glob("route_*.html"))

        assert len(map_files) == 2
        assert len(route_pages) == 2
        assert (maps_dir / "all_routes_map.html").exists()

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] run_route_presentation_pipeline (static v1)")
        print("-" * 70)
        print(f"Views root        : {views_root}")
        print(f"Route pages       : {len(route_pages)}")
        print(f"Route maps        : {len(map_files)}")
        print(f"Index page        : {index_html}")
        print(f"Combined map      : {maps_dir / 'all_routes_map.html'}")
        print(f"Results entries   : {len(all_results_route_list)}")
        print("-" * 70)


if __name__ == "__main__":
    test_run_route_presentation_pipeline_static_v1()
