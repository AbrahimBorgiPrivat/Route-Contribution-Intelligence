from typing import Dict, List, Tuple, FrozenSet, Literal, Optional
import numpy as np
from tqdm import tqdm

from libraries.utils.algorithm.single_route.coverage_cost import compute_coverage_change
from libraries.utils.algorithm.single_route.route_costs import compute_cost_change
from libraries.utils.algorithm.structural_heuristics.subset_evaluation import evaluate_subset
from libraries.config import SOLVERS, PROBLEM_TYPES, HPP_SOLVERS

def beam_expand(
    D: np.ndarray,
    R: List[int],
    p: List[int],
    E: float | List[float] | np.ndarray,
    APR: float,
    z: float,
    C_distance: Dict[FrozenSet[int], float],
    C2: Dict[FrozenSet[int], float],
    R_map: Dict[FrozenSet[int], List[int]],
    strict_order: bool,
    precheck: bool,
    deterministic: bool,
    k_all: int,
    k_max: int,
    B: int,
    L_R: float,
    *,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int = 5,
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    D_all: Optional[np.ndarray] = None,
    inner_models: Optional[List[Dict]] = None,
    inner_cache: Optional[Dict] = None,
    outer_cache: Optional[Dict] = None,
    ) -> Tuple[ Dict[FrozenSet[int], float],
                Dict[FrozenSet[int], float],
                Dict[FrozenSet[int], List[int]],
                Optional[Dict],
                Optional[Dict],
            ]:
    """
    Beam expansion for hybrid outlier detection.

    Parameters
    ----------
    D : Distance matrix used for cost evaluation.
        - Non-structured: address-to-address distance matrix.
        - Structured: outer (unit-to-unit) distance matrix.
    R : Full list of GLOBAL address indices.
    p : Demand / postboxes per address.
    E : Unit revenue.
        - Scalar: average unit revenue.
        - Vector: per-address unit revenue.
    APR : Distance cost per unit length.
    z : Threshold for candidate acceptance based on C2(S).
    C_distance : Mapping S → distance change ΔL(S).
    C2 : Mapping S → coverage change C2(S).
    R_map : Mapping S → resulting route.
        - Used to seed parent routes during expansion.
    strict_order : Routing mode selector.
        - True: fixed-order evaluation (Type 1).
        - False: re-optimization allowed (Type 2).
    precheck : Enable Type-1 precheck pruning.
        - If True: candidates with C2_pre ≤ z are discarded early.
    deterministic : Enforce deterministic solver behavior.
    k_all : Subset size where beam expansion starts.
    k_max : Maximum subset size considered.
    B : Beam width.
    L_R : Length of the original route.
    solver : Solver backend used for route optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    D_all : Address-level distance matrix (structured routing only).
    inner_models : Structured unit descriptions (structured routing only).
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
    # -------------------------
    # Initial beam
    # -------------------------
    if inner_cache is None:
        inner_cache = {}
    if outer_cache is None:
        outer_cache = {}
    n = len(R)
    C2_k_all = [S for S in C2 if len(S) == k_all]
    beam_candidates = [S for S in C2_k_all if C2[S] > z]
    topB = sorted(C2_k_all, key=lambda S: C2[S], reverse=True)[:B]
    B_prev = list(set(beam_candidates) | set(topB))
    # -------------------------
    # Main Beam Expansion Loop
    # -------------------------
    outer = tqdm(
        range(k_all + 1, min(k_max, n) + 1),
        desc="Beam k loop",
        position=0,
        leave=False,
    )
    for k in outer:
        B_next = []
        inner = tqdm(
            B_prev,
            desc=f"Beam expand k={k}",
            position=1,
            leave=False,
        )
        for S in inner:
            R_parent = R_map[S] if S in R_map else R
            for i in R:
                if i in S:
                    continue
                S_new = frozenset(set(S) | {i})
                if S_new in C2:
                    continue
                # ==================================================
                # TYPE 1 PRECHECK (always strict_order=True)
                # ==================================================
                if precheck:
                    pre_res = compute_cost_change(
                        D=D,
                        R=R_parent,
                        S=S_new,
                        strict_order=True,
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
                    )
                    C_pre = pre_res[0] if isinstance(pre_res, tuple) else pre_res
                    C2_pre = compute_coverage_change(
                        E, APR, p, R, S_new, C_pre
                    )
                    if C2_pre <= z:
                        continue
                # ==================================================
                # FULL EVALUATION (Type 1 / Type 2)
                # ==================================================
                C_distance, C2, R_map, inner_cache, outer_cache = evaluate_subset(
                    S=S_new,
                    D=D,
                    R=R,
                    p=p,
                    E=E,
                    APR=APR,
                    strict_order=strict_order,
                    L_R=L_R,
                    L_u=L_u,
                    problem_type=problem_type,
                    deterministic=deterministic,
                    solver=solver,
                    ortools_time_limit=ortools_time_limit,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                    precheck=precheck,
                    C_distance=C_distance,
                    C2=C2,
                    R_map=R_map,
                    D_all=D_all,
                    inner_models=inner_models,
                    inner_cache=inner_cache,
                    outer_cache=outer_cache,
                )
                B_next.append(S_new)
        if not B_next:
            break
        B_prev = sorted(B_next, key=lambda S: C2[S], reverse=True)[:B]
        if all(C2[S] <= z for S in B_prev):
            break
        inner.close()
    return C_distance, C2, R_map, inner_cache, outer_cache