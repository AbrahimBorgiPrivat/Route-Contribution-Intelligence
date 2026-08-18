import tempfile
from pathlib import Path

from libraries.utils.pipelines.pipelines.application.v1.run_route_data_pipeline import (
    run_route_data_pipeline,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


def test_run_route_data_pipeline_application_v1():
    # --------------------------------------------------
    # Skip if OSRM services are unavailable
    # --------------------------------------------------
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM SNAPPER service not running",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir) / "application_v1_data"

        # --------------------------------------------------
        # Run pipeline (UNDER TEST)
        # --------------------------------------------------
        route_outputs = run_route_data_pipeline(
            file_path="libraries/tests/_test_dataset/test_data.csv",
            save_dir=str(data_root),

            # --- algorithm ---
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
            type1_methods=["A", "B"],
            type2_methods=["A", "B"],

            # --- geometry ---
            allowed_highways=None,
            chunk_size_osm=2,
            chunk_size_osrm=25,
            use_rotated_side=True,
            offset_m=4.5,
            entry_angle_deg=60.0,
            exit_angle_deg=60.0,

            # --- routing ---
            route_type="both",
            start_routes=0,
            max_routes=2,

            # --- dataset ---
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

            # --- index ---
            kpi_mapping=[],
            use_data=True,
            index_filename="routes_index.json",
        )

        # --------------------------------------------------
        # Assertions: return value
        # --------------------------------------------------
        assert isinstance(route_outputs, list)
        assert len(route_outputs) == 2

        # --------------------------------------------------
        # Assertions: filesystem outputs
        # --------------------------------------------------
        routes_dir = data_root / "routes"
        index_json = data_root / "routes_index.json"

        assert routes_dir.exists()
        assert index_json.exists()

        # per-route folders
        route_folders = list(routes_dir.iterdir())
        assert len(route_folders) == 2

        for rf in route_folders:
            assert rf.is_dir()
            files = list(rf.iterdir())

            # Expect markers, routes, index JSON
            filenames = {f.name for f in files}
            assert any(name.endswith("_markers.geojson") for name in filenames)
            assert any(name.endswith("_route.geojson") for name in filenames)
            assert any(name.endswith(".json") and not name.endswith("_markers.geojson") for name in filenames)

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] run_route_data_pipeline (application v1)")
        print("-" * 70)
        print(f"Data root         : {data_root}")
        print(f"Routes generated  : {len(route_folders)}")
        print(f"Index file        : {index_json}")
        print(f"Route outputs     : {len(route_outputs)}")
        print("-" * 70)


if __name__ == "__main__":
    test_run_route_data_pipeline_application_v1()
