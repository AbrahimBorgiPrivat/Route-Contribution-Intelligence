from __future__ import annotations

import time
import numpy as np
from typing import List, Dict, Any, Optional, Literal

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import init_pipeline_context
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import prepare_route_and_matrices
from libraries.utils.pipelines.c_algorithm_layer.v1.pipeline_outlier_detection_for_route import run_outlier_detection_for_route
from libraries.utils.pipelines.d_application_layer.static.V1.pipeline_st_vone_route_presentation import present_single_route_static
from libraries.utils.pipelines.d_application_layer.static.V1.pipeline_st_vone_index_presentation import present_static_index
from libraries.config import TSP_SOLVERS, HPP_SOLVERS

def run_route_presentation_pipeline(
    file_path: str,
    *,
    file_seperator: str = ";",
    views_root: str = "./views/static/v1/",
    template_root: Optional[str] = None,
    E: float | List[float] | np.ndarray = 5.0,
    APR: float | Dict[str, Dict[str, float]] = 0.03,
    z: float = 0.0,
    k_max: int = 25,
    k_all: int = 1,
    B: int = 10,
    solver_tsp: TSP_SOLVERS = "ortools",
    solver_hpp: HPP_SOLVERS = "ortools",
    deterministic_tsp: bool = True,
    deterministic_hpp: bool = True,
    precheck: bool = True,
    A_kwargs: Optional[Dict[str, Any]] = None,
    B_kwargs: Optional[Dict[str, Any]] = None,
    U_kwargs: Optional[Dict[str, Any]] = None,
    type1_methods: Optional[List[str]] = None,
    type2_methods: Optional[List[str]] = None,
    ortools_time_limit: int = 5,
    initial_point_method: Optional[Dict[str, Any]] = None,
    allowed_highways: List[str] | None = None,
    chunk_size_osm:  Optional[str] = None,
    chunk_size_osrm: int = 50,
    use_rotated_side: bool = True,
    offset_m: float = 4.5,
    entry_angle_deg: float = 60.0,
    exit_angle_deg: float = 60.0,
    unit_entry_exit_strategy: str | None = None,
    route_type: Literal["type1", "type2", "both"] = "both",
    start_routes: Optional[int] = None,
    max_routes: Optional[int] = None,
    html_render: bool = True,
    col_map: Dict[str, Dict[str, str]] | None = None,
    kpi_mapping: List[Dict[str, Any]] | None = None,
):
    """
    Full static presentation pipeline (v1).

    Returns
    -------
    all_results_route_list : 
        Per-route outlier results.
    all_maps : 
        Map metadata (only if html_render=True).
    """
    t0 = time.perf_counter()
    # -----------------------------
    # Defaults
    # -----------------------------
    if col_map is None:
        col_map = {
            "route_id": {"name": "id"},
            "lon": {"name": "vejx"},
            "lat": {"name": "vejy"},
            "line_nr": {"name": "linienr"},
            "transform": {
                "convert_from": "EPSG:25832",
                "convert_to": "EPSG:4326",
            },
        }

    if kpi_mapping is None:
        kpi_mapping = []

    if type1_methods is None:
        type1_methods = ["A", "B", "Beam", "U"]

    if type2_methods is None:
        type2_methods = ["A", "B", "Beam", "U"]

    # -----------------------------
    # Step 1: Dataset context
    # -----------------------------
    ctx = init_pipeline_context(
        file_path=file_path,
        file_seperator=file_seperator,
        col_map=col_map,
        route_type=route_type,
        A_kwargs=A_kwargs,
        B_kwargs=B_kwargs,
        U_kwargs=U_kwargs,
        APR=APR,
        start_routes=start_routes,
        max_routes=max_routes,
    )

    print(f"[INFO] Processing {len(ctx.route_ids)} route(s)")

    all_maps: List[Dict[str, Any]] = []
    all_results: List[Dict[str, Any]] = []
    all_results_route_list: List[Dict[str, Any]] = []
    kpis: List[Dict[str, Any]] = []

    # -----------------------------
    # Step 2: Per-route pipeline
    # -----------------------------
    for route_id in ctx.route_ids:
        print(f"\n=== Processing Route {route_id} ===")
        t_route_start = time.perf_counter()

        # --- route preparation ---
        route_prep = prepare_route_and_matrices(
            route_id=route_id,
            df=ctx.df,
            APR=ctx.APR,
            solver_tsp=solver_tsp,
            solver_hpp=solver_hpp,
            deterministic_tsp=deterministic_tsp,
            deterministic_hpp=deterministic_hpp,
            allowed_highways= allowed_highways,
            chunk_size_osm=chunk_size_osm,
            chunk_size_osrm=chunk_size_osrm,
            use_rotated_side=use_rotated_side,
            offset_m=offset_m,
            entry_angle_deg=entry_angle_deg,
            exit_angle_deg=exit_angle_deg,
            unit_entry_exit_strategy=unit_entry_exit_strategy,
        )

        # --- outlier detection ---
        results_route_list = run_outlier_detection_for_route(
            route_id=route_prep.route_id,
            data=route_prep.data,
            APR_profile=route_prep.APR_profile,
            problem_type=route_prep.problem_type,
            strict_values=ctx.strict_values,
            type1_methods=type1_methods,
            type2_methods=type2_methods,
            E=E,
            z=z,
            k_max=k_max,
            k_all=k_all,
            B=B,
            L_u=route_prep.L_u,
            deterministic=route_prep.deterministic,
            precheck=precheck,
            solver=route_prep.solver,
            inner_solver=solver_hpp,
            ortools_time_limit=ortools_time_limit,
            initial_point_method=initial_point_method,
            A_kwargs=ctx.A_kwargs,
            B_kwargs=ctx.B_kwargs,
            U_kwargs=ctx.U_kwargs,
            t_route_start=t_route_start,
        )
        all_results_route_list.extend(results_route_list)

        # --- static presentation (per route) ---
        all_maps, all_results, kpis = present_single_route_static(
            route_id=route_id,
            data=route_prep.data,
            results_route_list=results_route_list,
            views_root=views_root,
            template_root=template_root,
            all_maps=all_maps,
            all_results=all_results,
            kpi_mapping=kpi_mapping,
            route_type=route_type,
            html_render=html_render,
        )

        t_route_end = time.perf_counter()
        print(
            f"Completed Route {route_id} in "
            f"{t_route_end - t_route_start:,.2f}s "
            f"using solver='{route_prep.solver}'"
        )

    # -----------------------------
    # Step 3: Index presentation
    # -----------------------------
    present_static_index(
        all_maps=all_maps,
        all_results=all_results,
        kpis=kpis,
        views_root=views_root,
        html_render=html_render,
        template_root=template_root,
    )

    t1 = time.perf_counter()
    print(
        f"\nPipeline completed in {t1 - t0:,.2f}s "
        f"for {len(ctx.route_ids)} route(s)"
    )

    return all_results_route_list, all_maps
