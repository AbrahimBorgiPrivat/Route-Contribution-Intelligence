import time
from typing import Any, Dict, List, Optional, Sequence
import numpy as np
from libraries.config import SOLVERS, HPP_SOLVERS
from libraries.utils.algorithm.single_route.core_algorithm import (
    find_outliers_hybrid,
    run_outlier_postprocessing,
)
from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    cache_exists,
    load_cache,
    save_cache,
)

# ============================================================
# v2 Route Outlier Pipeline (cache-aware)
# ============================================================

def run_outlier_detection_for_route_v2(
    route_id: Any,
    data: Dict[str, Any],
    APR_profile: Dict[str, Any],
    problem_type: str,
    strict_values: Sequence[bool],
    type1_methods: List[str],
    type2_methods: List[str],
    z: float,
    *,
    E: float | List[float] | np.ndarray = 5.0,
    k_max: int = 50,
    k_all: int = 1,
    B: int = 100,
    L_u: float | List[float] | np.ndarray = 0.0,
    deterministic: bool = True,
    precheck: bool = False,
    solver: SOLVERS = "ortools",
    inner_solver: Optional[HPP_SOLVERS] = None,
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    A_kwargs: Optional[Dict[str, Any]] = None,
    B_kwargs: Optional[Dict[str, Any]] = None,
    U_kwargs: Optional[Dict[str, Any]] = None,
    t_route_start: float = 0.0,
    c_cache_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
    """
    v2 cache-aware outlier pipeline.

    If c_cache_config is None or disabled → behaves exactly like v1.
    If enabled → uses structural cache (Type1 / Type2 separated).
    """
    # --------------------------------------------------------
    # Resolve revenue
    # --------------------------------------------------------
    if "revenue" in data["data"]:
        E_used = data["data"]["revenue"].to_numpy(dtype=float)
    else:
        E_used = E
    results_route_list: List[Dict[str, Any]] = []
    # --------------------------------------------------------
    # Main strict loop (UNCHANGED STRUCTURE)
    # --------------------------------------------------------
    for strict in strict_values:
        methods = type1_methods if strict else type2_methods
        use_cache = (
            c_cache_config is not None
            and c_cache_config.get("enabled", False)
        )
        # =====================================================
        # CASE 1: Cache disabled → classic hybrid
        # =====================================================
        if not use_cache:
            (
                coverage_change,
                distance_change,
                R_original,
                R_star,
                L_original,
                L_opt,
                S_outlier,
                C2_max,
                DG_original,
                DG_best,
            ) = find_outliers_hybrid(
                D=data["Distance_Matrix"],
                p=data["p"],
                E=E_used,
                APR=APR_profile["APR"],
                strict_order=strict,
                z=z,
                R=data["R"],
                k_max=k_max,
                k_all=k_all,
                B=B,
                L_u=L_u,
                problem_type=problem_type,
                deterministic=deterministic,
                precheck=precheck,
                solver=solver,
                inner_solver=inner_solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
                methods=methods,
                A_kwargs=A_kwargs,
                B_kwargs=B_kwargs,
                U_kwargs=U_kwargs,
                nodes=data["nodes"],
            )
        # =====================================================
        # CASE 2: Cache enabled
        # =====================================================
        else:
            base_path = c_cache_config["base_path"]
            label = c_cache_config["label"]
            cache_exist = cache_exists(
                base_path=base_path,
                label=label,
                route_id=route_id,
                strict=strict,
            )
            if cache_exist:
                # ----------------------------------------------
                # Load structural cache
                # ----------------------------------------------
                cache_payload = load_cache(
                    base_path=base_path,
                    label=label,
                    route_id=route_id,
                    strict=strict,
                )
                structured = cache_payload.get("structured") or {}
                inner_solver_cached = cache_payload.get("inner_solver", inner_solver)
                (
                    coverage_change,
                    distance_change,
                    R_original,
                    R_star,
                    L_original,
                    L_opt,
                    S_outlier,
                    C2_max,
                    DG_original,
                    DG_best,
                ) = run_outlier_postprocessing(
                    C2=None,
                    C_distance=cache_payload["C_distance_full"],
                    R=data["R"],
                    R_seq=cache_payload["R_seq"],
                    L_R=cache_payload["L_R"],
                    D=data["Distance_Matrix"],
                    p=data["p"],
                    E=E_used,
                    APR=APR_profile["APR"],
                    z=z,
                    L_u=L_u,
                    strict_order=strict,
                    problem_type=problem_type,
                    solver=solver,
                    deterministic=deterministic,
                    ortools_time_limit=ortools_time_limit,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                    D_outer=structured.get("D_outer"),
                    D_all=structured.get("D_all"),
                    inner_models=structured.get("inner_models"),
                    inner_solver=inner_solver_cached,
                    inner_cache=structured.get("inner_cache"),
                    outer_cache=structured.get("outer_cache"),
                    return_c_distance=False,
                )
            else:
                # ----------------------------------------------
                # Compute once + persist structural layer
                # ----------------------------------------------
                (result, cache_payload_struct) = find_outliers_hybrid(
                    D=data["Distance_Matrix"],
                    p=data["p"],
                    E=E_used,
                    APR=APR_profile["APR"],
                    strict_order=strict,
                    z=z,
                    R=data["R"],
                    k_max=k_max,
                    k_all=k_all,
                    B=B,
                    L_u=L_u,
                    problem_type=problem_type,
                    deterministic=deterministic,
                    precheck=precheck,
                    solver=solver,
                    inner_solver=inner_solver,
                    ortools_time_limit=ortools_time_limit,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                    methods=methods,
                    A_kwargs=A_kwargs,
                    B_kwargs=B_kwargs,
                    U_kwargs=U_kwargs,
                    nodes=data["nodes"],
                    return_c_distance=True,
                )
                (   coverage_change,
                    distance_change,
                    R_original,
                    R_star,
                    L_original,
                    L_opt,
                    S_outlier,
                    C2_max,
                    DG_original,
                    DG_best,
                ) = result
                save_cache(
                    base_path=base_path,
                    label=label,
                    route_id=route_id,
                    strict=strict,
                    C_distance_full=cache_payload_struct["C_distance_full"],
                    R_seq=R_original,
                    L_R=L_original,
                    D_outer=cache_payload_struct["D_outer"],
                    D_all=cache_payload_struct["D_all"],
                    inner_models=cache_payload_struct["inner_models"],
                    inner_solver=cache_payload_struct["inner_solver"],
                    inner_cache=cache_payload_struct["inner_cache"],
                    outer_cache=cache_payload_struct["outer_cache"],
                )
        # =====================================================
        # Append result 
        # =====================================================
        t_route_end = time.perf_counter()
        results_route_list.append(
            {
                "route_id": route_id,
                "strict_order": strict,
                "runtime": t_route_end - t_route_start,
                "model_type": "Type 1" if strict else "Type 2",
                "solver": solver,
                "deterministic": deterministic,
                "precheck": precheck,
                "DG_original": DG_original,
                "DG_best": DG_best,
                "L_original": L_original,
                "L_opt": L_opt,
                "C2_max": C2_max,
                "S_outlier": S_outlier,
                "coverage_change": coverage_change,
                "distance_change": distance_change,
                "APR": APR_profile["APR"],
                "R_original": R_original,
                "R_star": R_star,
                "profile": APR_profile,
                "problem_type": problem_type,
            }
        )
    return results_route_list
