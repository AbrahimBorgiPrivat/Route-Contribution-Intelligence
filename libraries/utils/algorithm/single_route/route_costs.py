import numpy as np
from typing import List, Set, Optional, Literal, Dict
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.route_solver_structured import solve_structured_route, apply_s_to_structured_model
from libraries.config import PROBLEM_TYPES, SOLVERS, STRUCTURED_PROBLEM_TYPES_SET, UNSTRUCTURED_PROBLEM_TYPES_SET, HPP_SOLVERS

def compute_cost_change(
    D: np.ndarray,
    R: List[int],
    S: Set[int],
    *,
    strict_order: bool = True,
    L_R: Optional[float] = None,
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS =  "ortools",
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    include_path: bool = False,
    D_all: np.ndarray | None = None,
    inner_models: List[Dict] | None = None,
    inner_cache: Optional[Dict] = None,
    outer_cache: Optional[Dict] = None,
) -> (
    float
    | tuple[float, List[int]]
    | tuple[float, Dict, Dict]
    | tuple[float, List[int], Dict, Dict]
):
    """
    Compute the change in route length after removing a subset of addresses.

    This function evaluates the marginal effect of removing S from an existing
    route, either under classical routing (TSP/HPP) or structured routing
    (OUT:TSP / OUT:HPP).

    ----------
    Parameters
    ----------
    D : Distance matrix used for routing.
        - Non-structured: address-to-address matrix.
        - Structured: outer (unit-to-unit) distance matrix.
    R : Original route as a list of GLOBAL address indices (route_numbers).
    S : Set of GLOBAL address indices to be removed.
    strict_order :
        If True, preserve the visiting order (Type 1).
        If False, re-optimize the route (Type 2).
    L_R : Length of the original route. If None, it is computed internally.
    L_u : Internal per-address cost(s), forwarded to Type 1 evaluation.
    problem_type :
        Routing problem type:
            - "TSP", "HPP"         : non-structured routing
            - "OUT:TSP", "OUT:HPP" : structured routing
    deterministic : If True, enforce deterministic solver behaviour (Type 2).
    solver : Solver backend to use for optimization.
    ortools_time_limit : Time limit (seconds) for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for non-structured HPP - For structured solvers is for the outer HPP solver.
    initial_point_method : Optional initialisation method  - For structured solvers is for the outer HPP solver.
    include_path : If True, also return the resulting route after removal.
    D_all : Structured Type 1 distance matrix (address-to-address).
    inner_models : Structured unit descriptions.
    inner_cache : Cache for inner structured HPP solutions.
    outer_cache : Cache for outer structured TSP/HPP solutions.

    -------
    Returns
    -------
    delta : Change in route length after removing S.
    R_seq_orig : Resulting route as a list of GLOBAL address indices. Returned only if include_path=True.
    inner_cache : Updated inner cache (structured problems only).
    outer_cache : Updated outer cache (structured problems only).
    """

    # ==================================================
    # NON-STRUCTURED CASE
    # ==================================================
    if problem_type in UNSTRUCTURED_PROBLEM_TYPES_SET:
        D = np.asarray(D)
        D_full = D[np.ix_(R, R)]
        R_local_full = list(range(len(R)))

        R_reduced_orig = [a for a in R if a not in S]

        # Edge case: everything removed
        if not R_reduced_orig:
            if L_R is None:
                _, L_R = solve_route(
                    D=D_full,
                    R=R_local_full,
                    strict_order=strict_order,
                    problem_type=problem_type,
                    L_u=L_u,
                    deterministic=deterministic,
                    solver=solver,
                    ortools_time_limit=ortools_time_limit,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                )
            return (-L_R, []) if include_path else -L_R

        # Original length
        if L_R is None:
            _, L_R = solve_route(
                D=D_full,
                R=R_local_full,
                strict_order=strict_order,
                problem_type=problem_type,
                L_u=L_u,
                deterministic=deterministic,
                solver=solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
            )

        # Reduce matrix
        pos = {orig: j for j, orig in enumerate(R)}
        idx = [pos[a] for a in R_reduced_orig]
        D_reduced = D_full[np.ix_(idx, idx)]
        R_local_reduced = list(range(len(R_reduced_orig)))

        # Reduced solve
        R_seq_local, L_R_reduced = solve_route(
            D=D_reduced,
            R=R_local_reduced,
            strict_order=strict_order,
            problem_type=problem_type,
            L_u=L_u,
            deterministic=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
        )

        delta = L_R_reduced - L_R

        if include_path:
            R_seq_orig = [R_reduced_orig[i] for i in R_seq_local]
            return delta, R_seq_orig

        return delta

    # ==================================================
    # STRUCTURED CASE
    # ==================================================
    elif problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        if D_all is None or inner_models is None:
            raise ValueError(
                "D_all and inner_models must be provided for structured problems."
            )
        # --------------------------------------------------
        # Original structured route length
        # --------------------------------------------------
        if L_R is None:
            _, L_R, inner_cache, outer_cache = solve_structured_route(
                D_outer=D,
                D_all=D_all,
                R=list(R),
                inner_models=inner_models,
                strict_order=strict_order,
                problem_type=problem_type,
                solver=solver,
                inner_solver=inner_solver,
                deterministic=deterministic,
                ortools_time_limit=ortools_time_limit,
                inner_cache=inner_cache,
                outer_cache=outer_cache,
            )

        # --------------------------------------------------
        # Apply removal S
        # --------------------------------------------------
        (
            D_outer_new,
            D_all_new,
            R_local_reduced,
            inner_models_new,
            _,
            address_index_map,
        ) = apply_s_to_structured_model(
            D_outer=D,
            D_all=D_all,
            R=R,
            inner_models=inner_models,
            S=S,
        )

        # --------------------------------------------------
        # Solve reduced structured route
        # --------------------------------------------------
        R_seq_local, L_R_reduced, inner_cache, outer_cache = solve_structured_route(
            D_outer=D_outer_new,
            D_all=D_all_new,
            R=R_local_reduced,
            inner_models=inner_models_new,
            strict_order=strict_order,
            problem_type=problem_type,
            solver=solver,
            inner_solver=inner_solver,
            deterministic=deterministic,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )

        delta = L_R_reduced - L_R

        if include_path:
            inv_address_index_map = {
                new: old for old, new in address_index_map.items()
            }
            R_seq_orig = [inv_address_index_map[i] for i in R_seq_local]
            return delta, R_seq_orig, inner_cache, outer_cache
        return delta, inner_cache, outer_cache
    else:
        raise ValueError(f"Unknown problem_type: {problem_type}")