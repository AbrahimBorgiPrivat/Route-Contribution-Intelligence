from typing import Dict, FrozenSet, List, Tuple, Optional

from libraries.utils.algorithm.single_route.coverage_cost import compute_coverage_change
from libraries.utils.algorithm.single_route.route_costs import compute_cost_change
from libraries.config import SOLVERS, PROBLEM_TYPES, STRUCTURED_PROBLEM_TYPES_SET, HPP_SOLVERS

def evaluate_subset(
    S: FrozenSet[int],
    D,
    R: List[int],
    p,
    E,
    APR,
    strict_order: bool,
    L_R,
    L_u,
    *,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    precheck: bool = True,
    C_distance: Dict[FrozenSet[int], float] | None = None,
    C2: Dict[FrozenSet[int], float] | None = None,
    R_map: Dict[FrozenSet[int], List[int]] | None = None,
    D_all=None,
    inner_models=None,
    inner_cache: Optional[Dict] = None,
    outer_cache: Optional[Dict] = None,
    ) -> Tuple[Dict, Dict, Dict, Optional[Dict], Optional[Dict]]:
    """
    Evaluate a single candidate subset S for outlier detection.

    Computes the marginal route-length change ΔL(S) and corresponding coverage
    change C2(S) for a given subset S ⊆ R. This function is the shared evaluation
    kernel used by full enumeration, hybrid heuristics (Method A / B), beam
    expansion, and the final full-set fallback.

    ----------
    Parameters
    ----------
    S : Candidate subset of addresses to remove.
    D : Distance matrix used for cost evaluation.
        - Non-structured: address-to-address distance matrix.
        - Structured: outer (unit-to-unit) distance matrix.
    R : Full list of GLOBAL address indices.
    p : Demand / postboxes per address.
    E : Unit revenue.
        - Scalar: average unit revenue.
        - Vector: per-address unit revenue.
    APR : Distance cost per unit length.
    strict_order : Routing mode selector.
        - True: fixed-order evaluation (Type 1).
        - False: re-optimization allowed (Type 2).
    L_R : Length of the original route.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
    deterministic : Enforce deterministic solver behavior.
    solver : Solver backend used for optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    precheck : Enable precheck behavior.
        - If True: resulting route after removal is also computed.
    C_distance : Mapping S → distance change ΔL(S).
    C2 : Mapping S → coverage change C2(S).
    R_map : Mapping S → resulting route.
        - Only populated if precheck=True.
    D_all : Address-level distance matrix (structured routing only).
    inner_models : Structured unit descriptions.
    inner_cache : Cache for inner structured route solutions.
    outer_cache : Cache for outer structured route solutions.

    -------
    Returns
    -------
    C_distance : Updated mapping from subset S to distance change.
    C2 : Updated mapping from subset S to coverage change.
    R_map : Updated mapping from subset S to resulting route.
    inner_cache : Updated inner cache (structured problems only).
    outer_cache : Updated outer cache (structured problems only).
    """

    # --------------------------------------------------
    # Cost change
    # --------------------------------------------------
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        if precheck:
            delta, R_s_pre, inner_cache, outer_cache = compute_cost_change(
                D=D,
                R=R,
                S=S,
                strict_order=strict_order,
                L_R=L_R,
                L_u=L_u,
                problem_type=problem_type,
                deterministic=deterministic,
                solver=solver,
                inner_solver=inner_solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
                include_path=True,
                D_all=D_all,
                inner_models=inner_models,
                inner_cache=inner_cache,
                outer_cache=outer_cache,
            )
            R_map[S] = R_s_pre
        else:
            delta, inner_cache, outer_cache = compute_cost_change(
                D=D,
                R=R,
                S=S,
                strict_order=strict_order,
                L_R=L_R,
                L_u=L_u,
                problem_type=problem_type,
                deterministic=deterministic,
                solver=solver,
                inner_solver=inner_solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
                include_path=False,
                D_all=D_all,
                inner_models=inner_models,
                inner_cache=inner_cache,
                outer_cache=outer_cache,
            )
    else:
        if precheck:
            delta, R_s_pre = compute_cost_change(
                D=D,
                R=R,
                S=S,
                strict_order=strict_order,
                L_R=L_R,
                L_u=L_u,
                problem_type=problem_type,
                deterministic=deterministic,
                solver=solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
                include_path=True,
            )
            R_map[S] = R_s_pre
        else:
            delta = compute_cost_change(
                D=D,
                R=R,
                S=S,
                strict_order=strict_order,
                L_R=L_R,
                L_u=L_u,
                problem_type=problem_type,
                deterministic=deterministic,
                solver=solver,
                ortools_time_limit=ortools_time_limit,
                fixed_endpoints=fixed_endpoints,
                initial_point_method=initial_point_method,
                include_path=False,
            )
    # --------------------------------------------------
    # Coverage change
    # --------------------------------------------------
    C_distance[S] = delta
    C2[S] = compute_coverage_change(E, APR, p, R, S, delta)
    return C_distance, C2, R_map, inner_cache, outer_cache
