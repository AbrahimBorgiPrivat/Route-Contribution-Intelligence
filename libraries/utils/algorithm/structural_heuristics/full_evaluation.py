import itertools
from typing import Dict, FrozenSet, List
import numpy as np
from tqdm import tqdm

from libraries.utils.algorithm.structural_heuristics.subset_evaluation import evaluate_subset
from libraries.config import PROBLEM_TYPES, SOLVERS, STRUCTURED_PROBLEM_TYPES_SET, HPP_SOLVERS

def full_set_evaluation(
    D: np.ndarray,
    R: List[int],
    p: List[float],
    E: float | List[float] | np.ndarray,
    APR: float,
    L_R: float,
    strict_order: bool,
    k_all: int,
    *,
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    precheck: bool = False,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    D_all: np.ndarray | None = None,
    inner_models: List[Dict] | None = None,
    inner_cache: Dict | None = None,
    outer_cache: Dict | None = None,
    ) -> (tuple[Dict[FrozenSet[int], float], Dict[FrozenSet[int], float]]
        | tuple[Dict[FrozenSet[int], float], Dict[FrozenSet[int], float], Dict[FrozenSet[int], List[int]]]
        | tuple[Dict[FrozenSet[int], float], Dict[FrozenSet[int], float], Dict, Dict]
        | tuple[Dict[FrozenSet[int], float], Dict[FrozenSet[int], float], Dict[FrozenSet[int], List[int]], Dict, Dict]
    ):
    """
    Phase 1: Exhaustive evaluation of n removal sets.

    Parameters
    ----------
    D : Distance matrix used for routing.
        - Non-structured: address-to-address matrix.
        - Structured: outer (unit-to-unit) distance matrix.
    R : Original route as a list of GLOBAL address indices.
    p : Per-address coverage weights.
    E : Coverage scaling parameter(s).
    APR : Average profit rate used in coverage computation.
    L_R : Length of the original route.
    strict_order :
        If True, preserve the visiting order (Type 1).
        If False, re-optimize the route (Type 2).
    k_all : Maximum subset cardinality |S| to evaluate exhaustively.
    L_u : Internal per-address cost(s), forwarded to Type 1 evaluation.
    problem_type :
            - "TSP", "HPP"         : non-structured routing
            - "OUT:TSP", "OUT:HPP" : structured routing
    deterministic : If True, enforce deterministic solver behaviour.
    precheck : If True, also compute and store the resulting route after removal.
    solver : Solver backend to use for optimization.
    ortools_time_limit : Time limit (seconds) for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional initialization method for solvers.
    D_all : Structured Type 1 distance matrix (address-to-address).
    inner_models : Structured unit descriptions.
    inner_cache : Cache for inner structured HPP solutions.
    outer_cache : Cache for outer structured TSP/HPP solutions.

    Returns
    -------
    C_distance : Mapping from removal set S to route-length change ΔL(S).
    C2 : Mapping from removal set S to coverage change C₂(S).
    R_map : Mapping from removal set S to resulting GLOBAL route after removal.
    inner_cache : Updated cache for inner structured HPP solutions.
    outer_cache : Updated cache for outer structured TSP/HPP solutions.
    """
    n = len(R)
    C_distance: Dict[FrozenSet[int], float] = {}
    C2: Dict[FrozenSet[int], float] = {}
    R_map: Dict[FrozenSet[int], List[int]] = {}
    outer = tqdm(
        range(1, min(k_all, n) + 1),
        desc="k loop",
        position=0,
        leave=False,
    )
    for k in outer:
        inner = tqdm(
            itertools.combinations(R, k),
            desc=f"Comb(k={k})",
            position=1,
            leave=False,
        )
        for S_tuple in inner:
            S = frozenset(S_tuple)
            if S in C2:
                continue
            C_distance, C2, R_map, inner_cache, outer_cache = evaluate_subset(
                S=S,
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
                inner_solver=inner_solver,
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
        inner.close()
    # --------------------------------------------------
    # Return according to contract
    # --------------------------------------------------
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        if precheck:
            return C_distance, C2, R_map, inner_cache, outer_cache
        return C_distance, C2, inner_cache, outer_cache
    if precheck:
        return C_distance, C2, R_map
    return C_distance, C2
