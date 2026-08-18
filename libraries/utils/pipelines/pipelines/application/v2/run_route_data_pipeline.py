from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import init_pipeline_context
from libraries.utils.pipelines.a_context_layer.pipeline_build_config import _build_v2_config
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_existing_route_guard import route_output_exists
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import prepare_route_and_matrices
from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_outlier_detection_for_route_v2 import run_outlier_detection_for_route_v2
from libraries.utils.pipelines.d_application_layer.application.V1.pipeline_ap_vone_route_data import build_single_route_data
from libraries.utils.pipelines.d_application_layer.application.v2.pipeline_ap_vtwo_registry import build_v2_registry

def run_route_data_pipeline_v2(
    file_path: str,
    *,
    file_seperator: str = ";",
    route_type: str = "both",
    start_routes: Optional[int] = None,
    max_routes: Optional[int] = None,
    E: float | List[float] | np.ndarray = 5.0,
    z: float = 0.0,
    k_max: int = 25,
    k_all: int = 1,
    B: int = 10,
    solver_tsp: str = "ortools",
    solver_hpp: str = "ortools",
    deterministic_tsp: bool = True,
    deterministic_hpp: bool = True,
    precheck: bool = True,
    ortools_time_limit: int = 5,
    initial_point_method: Optional[Dict[str, Any]] = None,
    type1_methods: Optional[List[str]] = None,
    type2_methods: Optional[List[str]] = None,
    A_kwargs: Optional[Dict[str, Any]] = None,
    B_kwargs: Optional[Dict[str, Any]] = None,
    U_kwargs: Optional[Dict[str, Any]] = None,
    allowed_highways: Optional[List[str]] = None,
    chunk_size_osm: Optional[int] = None,
    chunk_size_osrm: int = 50,
    use_rotated_side: bool = True,
    offset_m: float = 4.5,
    entry_angle_deg: float = 60.0,
    exit_angle_deg: float = 60.0,
    unit_entry_exit_strategy: Optional[str] = None,
    col_map: Optional[Dict[str, Any]] = None,
    label_list: List[Dict[str, Any]] = None,
    APR_profiles: List[Dict[str, Any]] = None,
    revenue_list: List[Dict[str, Any]] = None,
    save_root: str = "./views/application/v2/data",
    skip_if_output_exists: bool = True,
):
    if type1_methods is None:
        type1_methods = ["A", "B", "U"]
    if type2_methods is None:
        type2_methods = ["A", "B", "U"]
    if col_map is None:
        raise ValueError("col_map must be provided")
    if label_list is None:
        raise ValueError("label_list must be provided")
    if APR_profiles is None:
        raise ValueError("APR_profiles must be provided")
    if revenue_list is None:
        raise ValueError("revenue_list must be provided")

    base_save_dir = Path(save_root)

    # ---------------------------------------------------------
    # Build base flat config (default layer)
    # ---------------------------------------------------------
    default_runner = {
        "input": {
            "file_path": file_path,
            "file_seperator": file_seperator,
        },
        "routing": {
            "route_type": route_type,
            "start_routes": start_routes,
            "max_routes": max_routes,
        },
        "algorithm": {
            "E": E,
            "z": z,
            "k_max": k_max,
            "k_all": k_all,
            "B": B,
            "solver_tsp": solver_tsp,
            "solver_hpp": solver_hpp,
            "deterministic_tsp": deterministic_tsp,
            "deterministic_hpp": deterministic_hpp,
            "precheck": precheck,
            "ortools_time_limit": ortools_time_limit,
            "initial_point_method": initial_point_method,
            "type1_methods": type1_methods,
            "type2_methods": type2_methods,
            "A_kwargs": A_kwargs,
            "B_kwargs": B_kwargs,
            "U_kwargs": U_kwargs,
        },
        "geometry": {
            "allowed_highways": allowed_highways,
            "chunk_size_osm": chunk_size_osm,
            "chunk_size_osrm": chunk_size_osrm,
            "use_rotated_side": use_rotated_side,
            "offset_m": offset_m,
            "entry_angle_deg": entry_angle_deg,
            "exit_angle_deg": exit_angle_deg,
            "unit_entry_exit_strategy": unit_entry_exit_strategy,
        },
        "mappings": {
            "col_map": col_map
        }
    }
    route_outputs: List[Dict[str, Any]] = []
    # ---------------------------------------------------------
    # Multi-scenario loops
    # ---------------------------------------------------------
    for label_cfg in label_list:
        label_name = label_cfg["c_cache_config"]["label"]
        c_cache_config = label_cfg.get("c_cache_config")

        for apr_cfg in APR_profiles:
            apr_label = apr_cfg["APR Label"]

            for revenue_cfg in revenue_list:
                week_label = revenue_cfg["revenue label"]

                # -------------------------------------------------
                # Build final config using helper (correct precedence)
                # -------------------------------------------------
                final_cfg = _build_v2_config(
                    default_runner=default_runner,
                    label_cfg=label_cfg,
                    apr_cfg=apr_cfg,
                    revenue_cfg=revenue_cfg,
                )

                # -------------------------------------------------
                # Dataset context
                # -------------------------------------------------
                ctx = init_pipeline_context(
                    file_path=final_cfg["input"]["file_path"],
                    file_seperator=final_cfg["input"]["file_seperator"],
                    col_map=final_cfg["mappings"]["col_map"],
                    route_type=final_cfg["routing"]["route_type"],
                    A_kwargs=final_cfg.get("algorithm", {}).get("A_kwargs"),
                    B_kwargs=final_cfg.get("algorithm", {}).get("B_kwargs"),
                    U_kwargs=final_cfg.get("algorithm", {}).get("U_kwargs"),
                    APR=final_cfg["algorithm"]["APR"],
                    selector=label_cfg.get("selector"),
                    start_routes=final_cfg["routing"]["start_routes"],
                    max_routes=final_cfg["routing"]["max_routes"],
                )

                label_df = ctx.df
                route_ids = ctx.route_ids

                for route_id in route_ids:

                    t_start = time.perf_counter()
                    print(
                        f"Starting Route {route_id} "
                        f" with label='{label_name}', APR='{apr_label}', week='{week_label}'"
                    )
                    if skip_if_output_exists and route_output_exists(
                        save_root=base_save_dir,
                        label_name=label_name,
                        route_id=route_id,
                        apr_label=apr_label,
                        week_label=week_label,
                    ):
                        print(
                            f"Skipping Route {route_id} "
                            f"with label='{label_name}', APR='{apr_label}', week='{week_label}' "
                            f"because output already exists."
                        )
                        continue
                    route_prep = prepare_route_and_matrices(
                        route_id=route_id,
                        df=label_df,
                        APR=ctx.APR,
                        solver_tsp=final_cfg["algorithm"]["solver_tsp"],
                        solver_hpp=final_cfg["algorithm"]["solver_hpp"],
                        deterministic_tsp=final_cfg["algorithm"]["deterministic_tsp"],
                        deterministic_hpp=final_cfg["algorithm"]["deterministic_hpp"],
                        allowed_highways=final_cfg.get("geometry", {}).get("allowed_highways"),
                        chunk_size_osm=final_cfg.get("geometry", {}).get("chunk_size_osm"),
                        chunk_size_osrm=final_cfg.get("geometry", {}).get("chunk_size_osrm"),
                        use_rotated_side=final_cfg.get("geometry", {}).get("use_rotated_side"),
                        offset_m=final_cfg.get("geometry", {}).get("offset_m"),
                        entry_angle_deg=final_cfg.get("geometry", {}).get("entry_angle_deg"),
                        exit_angle_deg=final_cfg.get("geometry", {}).get("exit_angle_deg"),
                        unit_entry_exit_strategy=final_cfg.get("geometry", {}).get("unit_entry_exit_strategy"),
                    )
                    results_route_list = run_outlier_detection_for_route_v2(
                        route_id=route_prep.route_id,
                        data=route_prep.data,
                        APR_profile=route_prep.APR_profile,
                        problem_type=route_prep.problem_type,
                        strict_values=ctx.strict_values,
                        type1_methods=final_cfg["algorithm"]["type1_methods"],
                        type2_methods=final_cfg["algorithm"]["type2_methods"],
                        E=final_cfg["algorithm"]["E"],
                        z=final_cfg["algorithm"]["z"],
                        k_max=final_cfg["algorithm"]["k_max"],
                        k_all=final_cfg["algorithm"]["k_all"],
                        B=final_cfg["algorithm"]["B"],
                        L_u=route_prep.L_u,
                        deterministic=route_prep.deterministic,
                        precheck=final_cfg["algorithm"]["precheck"],
                        solver=route_prep.solver,
                        inner_solver=final_cfg["algorithm"]["solver_hpp"],
                        ortools_time_limit=final_cfg["algorithm"]["ortools_time_limit"],
                        initial_point_method=final_cfg["algorithm"]["initial_point_method"],
                        A_kwargs=final_cfg.get("algorithm", {}).get("A_kwargs"),
                        B_kwargs=final_cfg.get("algorithm", {}).get("B_kwargs"),
                        U_kwargs=final_cfg.get("algorithm", {}).get("U_kwargs"),
                        t_route_start=t_start,
                        c_cache_config=c_cache_config,
                    )

                    save_dir = (
                        base_save_dir
                        / label_name
                        / str(route_id)
                        / apr_label
                        / week_label
                    )

                    output = build_single_route_data(
                        route_id=str(route_id),
                        route_data=route_prep.data,
                        results_route_list=results_route_list,
                        save_dir=str(save_dir),
                        E=final_cfg["algorithm"]["E"],
                        problem_type=route_prep.problem_type,
                        structure="v2"
                    )
                    route_outputs.append(output)
                    t_route_end = time.perf_counter()
                    print(
                        f"Completed Route {route_id} "
                        f"in {t_route_end - t_start:,.2f}s"
                        f" using solver='{route_prep.solver}'"
                        f" with label='{label_name}', APR='{apr_label}', week='{week_label}'"
                    )
    registry_path = build_v2_registry(
        save_dir=str(base_save_dir),
        registry_filename="registry.json",
        label_list=label_list,
        APR_profiles=APR_profiles,
        revenue_list=revenue_list,
    )
    print(f"\n[V2] Multi-scenario pipeline completed. Registry written to: {registry_path}")
