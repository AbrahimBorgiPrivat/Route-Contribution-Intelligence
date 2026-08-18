from typing import Dict, FrozenSet, List, Optional, Set
import numpy as np
from tqdm import tqdm

from libraries.utils.algorithm.structural_heuristics.subset_evaluation import evaluate_subset
from libraries.config import PROBLEM_TYPES, SOLVERS, HPP_SOLVERS

def _build_union_candidates(
    promising_sets: List[FrozenSet[int]],
    *,
    max_combination_size: Optional[int] = None,
    max_union_size: Optional[int] = None,
    min_union_size: Optional[int] = None,
) -> Set[FrozenSet[int]]:
    """
    Build all k-way unions of promising sets (k >= 2),
    with aggressive pruning using incremental unions.
    """
    if len(promising_sets) < 2:
        return set()
    sets = sorted(promising_sets, key=len)
    n = len(sets)
    k_max = max_combination_size or n
    results: Set[FrozenSet[int]] = set()
    def backtrack(
        start: int,
        chosen: int,
        current_union: FrozenSet[int],
    ):
        if chosen >= 2:
            results.add(current_union)
        if chosen == k_max:
            return
        for i in range(start, n):
            s = sets[i]
            new_union = current_union | s
            if max_union_size is not None and len(new_union) > max_union_size:
                continue
            if min_union_size is not None and len(new_union) < min_union_size:
                continue
            backtrack(
                i + 1,
                chosen + 1,
                new_union,
            )
    for i in tqdm(range(n),desc="Building union candidates",leave=False):
        backtrack(
            i + 1,
            1,
            sets[i],
        )
    return results

def run_union_candidate_generation(
    D,
    R: List[int],
    p: List[float],
    E: float | List[float],
    APR: float,
    z: float,
    strict_order: bool,
    L_R: float,
    L_u: float | List[float],
    *,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    precheck: bool = True,
    U_kwargs: Dict | None = None,
    C_distance: Dict[FrozenSet[int], float] | None = None,
    C2: Dict[FrozenSet[int], float] | None = None,
    R_map: Dict[FrozenSet[int], List[int]] | None = None,
    D_all: np.ndarray | None = None,
    inner_models: Optional[List[Dict]] = None,
    inner_cache: Optional[Dict] = None,
    outer_cache: Optional[Dict] = None,
) -> tuple[
    Dict[FrozenSet[int], float],
    Dict[FrozenSet[int], float],
    Dict[FrozenSet[int], List[int]],
    Dict,
    Dict,
]:
    """
    Union-based candidate generation for outlier detection.
    This method evaluates unions of previously accepted subsets S with C2(S) > z.
    
    Parameters
    ----------
    D : Distance matrix used for cost evaluation.
    R : Full list of GLOBAL address indices.
    p : Postboxes / demand per address.
    E : Average unit revenue or per-address unit revenues.
    APR : Distance cost per unit length.
    z : Threshold for accepting promising subsets based on C2(S).
    strict_order : Routing mode selector (Type 1 vs Type 2).
    L_R : Length of the original route.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
    deterministic : Enforce deterministic solver behavior.
    solver : Solver backend used for route optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    precheck : If True, store resulting routes for evaluated subsets.
    U_kwargs : Optional parameters controlling union construction
        (e.g. maximum number of subsets combined, maximum union size).
    C_distance : Mapping from subset S to distance change ΔL(S).
    C2 : Mapping from subset S to coverage change C2(S).
    R_map : Mapping from subset S to resulting route.
    D_all : Structured address-to-address distance matrix (structured problems only).
    inner_models : Structured unit descriptions (structured problems only).
    inner_cache : Cache for inner structured route solutions.
    outer_cache : Cache for outer structured route solutions.

    Returns
    -------
    C_distance : Updated mapping from subset S to distance change.
    C2 : Updated mapping from subset S to coverage change.
    R_map : Updated mapping from subset S to resulting route.
    inner_cache : Updated inner cache (structured problems only).
    outer_cache : Updated outer cache (structured problems only).
    """
    if C_distance is None:
        C_distance = {}
    if C2 is None:
        C2 = {}
    if R_map is None:
        R_map = {}
    if inner_cache is None:
        inner_cache = {}
    if outer_cache is None:
        outer_cache = {}
    if U_kwargs is None:
        U_kwargs = {}
    max_combination_size = U_kwargs.get("max_combination_size")
    max_union_size = U_kwargs.get("max_union_size")
    min_union_size = U_kwargs.get("min_union_size")
    # --------------------------------------------------
    # Step 1: collect promising subsets
    # --------------------------------------------------
    promising_sets = [S for S, val in C2.items() if val > z]
    # --------------------------------------------------
    # Step 2: construct union candidates
    # --------------------------------------------------
    union_candidates = _build_union_candidates(
        promising_sets,
        max_combination_size=max_combination_size,
        max_union_size=max_union_size,
        min_union_size=min_union_size,
    )
    if not union_candidates:
        return C_distance, C2, R_map, inner_cache, outer_cache
    # --------------------------------------------------
    # Step 3: evaluate unseen unions
    # --------------------------------------------------
    for S_new in tqdm(union_candidates,desc="Method U unions",leave=False):
        if S_new in C2:
            continue
        (
            C_distance,
            C2,
            R_map,
            inner_cache,
            outer_cache,
        ) = evaluate_subset(
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
    return C_distance, C2, R_map, inner_cache, outer_cache
