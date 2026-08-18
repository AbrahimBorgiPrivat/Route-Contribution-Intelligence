import copy
import os
import webbrowser
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
from libraries.utils.visualization.map_pipeline import build_route_map
from libraries.utils.visualization.html_generator import render_route_page
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
            "OUT:TSP": [0, 1, 2],
        },
    },
    "route_type": "both",
    "APR": 0.03,
    "start_routes": None,
    "max_routes": None,
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
    "U_kwargs": {}
}


def test_render_route_page():
    # --------------------------------------------------
    # Skip if OSRM and OSM services are unavailable
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

    # --------------------------------------------------
    # Step 1: pipeline context
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
    # Step 4: build map (required input)
    # --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        views_root = Path(tmpdir)

        # --- inject test template ---
        template_src = Path(
            "libraries/tests/_test_templates/templates/route_page.html"
        )
        assert template_src.exists(), "Test route_page.html template missing"

        template_dst = views_root / "templates"
        template_dst.mkdir(parents=True)
        (template_dst / "route_page.html").write_text(
            template_src.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        map_info = build_route_map(
            route_id=str(route_id),
            route_data=route_prep.data,
            results_list=results,
            views_root=str(views_root),
            saved_or_show="save",
        )

        # --------------------------------------------------
        # Step 5: render route page (UNDER TEST)
        # --------------------------------------------------
        out = render_route_page(
            route_id=str(route_id),
            map_file=map_info["map_file"],
            results=results,
            saved_or_show="save",
            views_root=str(views_root),
        )

        # --------------------------------------------------
        # Assertions
        # --------------------------------------------------
        assert isinstance(out, dict)
        assert "html_path" in out

        html_path = views_root / "routes" / f"route_{route_id}.html"
        assert html_path.exists()

        html = html_path.read_text(encoding="utf-8")

        assert str(route_id) in html
        assert map_info["map_file"] in html
        assert "TSP" in html or "HPP" in html or "OUT:TSP" in html or "OUT:HPP" in html
        assert f"Rute {route_id}" in html
        assert "<iframe" in html
        assert "Type 1 Model" in html or "Type 2 Model" in html

        # --------------------------------------------------
        # PRINTS (intentional)
        # --------------------------------------------------
        print("\n[TEST] render_route_page")
        print("-" * 70)
        print(f"Route ID        : {route_id}")
        print(f"HTML path       : {html_path}")
        print("HTML preview:")
        print(html[:400])
        print("-" * 70)

def test_render_route_page_show_mode(monkeypatch, tmp_path) -> None:
    """
    Coverage test:
    Exercise SHOW branch (lines 42–48) in render_route_page.
    """
    print("\n=== TEST CASE: render_route_page SHOW mode ===")
    views_root = tmp_path
    templates_dir = views_root / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "route_page.html").write_text(
        """
        <html>
            <body>
                <h1>Rute {{ route_id }}</h1>
                <iframe src="{{ map_file }}"></iframe>
            </body>
        </html>
        """,
        encoding="utf-8",
    )
    route_id = "TEST_ROUTE"
    map_file = "maps/test_map.html"
    results = [{"dummy": True}]
    opened_urls = []
    def fake_open(url):
        opened_urls.append(url)
        return True
    monkeypatch.setattr(webbrowser, "open", fake_open)
    out = render_route_page(
        route_id=route_id,
        map_file=map_file,
        results=results,
        saved_or_show="show",
        views_root=str(views_root),
    )
    assert isinstance(out, dict)
    assert "html_path" in out
    html_path = out["html_path"]
    assert os.path.exists(html_path)
    html = Path(html_path).read_text(encoding="utf-8")
    assert route_id in html
    assert map_file in html
    assert "<iframe" in html
    assert len(opened_urls) == 1
    assert opened_urls[0].startswith("file://")

if __name__ == "__main__":
    test_render_route_page()
