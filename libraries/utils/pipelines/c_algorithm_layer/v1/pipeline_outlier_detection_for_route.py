
import time
import numpy as np
from typing import Any, Dict, List, Optional, Sequence
from libraries.utils.algorithm.single_route.core_algorithm import find_outliers_hybrid
from libraries.config import SOLVERS, HPP_SOLVERS

def run_outlier_detection_for_route(
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
    precheck: bool  = False,
    solver: SOLVERS = "ortools",
    inner_solver: Optional[HPP_SOLVERS] =  None,
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    A_kwargs:  Optional[Dict[str, Any]] = None,
    B_kwargs: Optional[Dict[str, Any]] = None,
    U_kwargs: Optional[Dict[str, Any]] = None,
    t_route_start: float = 0.0,
) -> List[Dict[str, Any]]:
    # ----------------------------------------
    # Resolve E (revenue-aware)
    # ----------------------------------------
    if "revenue" in data['data']:
        E_used = data['data']["revenue"].to_numpy(dtype=float)
    else:
        E_used = E

    results_route_list: List[Dict[str, Any]] = []
    
    for strict in strict_values:
        methods = type1_methods if strict else type2_methods

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
            inner_solver = inner_solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints = fixed_endpoints,
            initial_point_method=initial_point_method,
            methods=methods,
            A_kwargs=A_kwargs,
            B_kwargs=B_kwargs,
            U_kwargs=U_kwargs,
            nodes=data["nodes"],
        )
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
