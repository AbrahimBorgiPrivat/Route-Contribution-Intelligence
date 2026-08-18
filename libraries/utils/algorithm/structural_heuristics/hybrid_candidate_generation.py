from typing import Dict, List, FrozenSet, Optional, Literal
from tqdm import tqdm
import numpy as np

from libraries.config import HYBRID_METHODS
from libraries.utils.algorithm.structural_heuristics.greedy_peripheral_clusters import greedy_peripheral_clusters
from libraries.utils.algorithm.structural_heuristics.find_marginal_blocks import find_marginal_blocks
from libraries.utils.algorithm.structural_heuristics.beam_method import beam_expand
from libraries.utils.algorithm.structural_heuristics.subset_evaluation import evaluate_subset
from libraries.utils.algorithm.structural_heuristics.union_helpers import run_union_candidate_generation
from libraries.config import PROBLEM_TYPES, SOLVERS, STRUCTURED_PROBLEM_TYPES_SET, HPP_SOLVERS

def run_hybrid_candidate_generation(
    D,
    R: List[int],
    R_seq: List[int],
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
    methods: List[HYBRID_METHODS] = ["A", "B", "Beam", "U"],
    A_kwargs: Dict | None = None,
    B_kwargs: Dict | None = None,
    U_kwargs: Dict | None = None,
    precheck: bool = True,
    k_all: int = 1,
    k_max: int = 50,
    B: int = 25,
    C_distance: Dict[FrozenSet[int], float] | None = None,
    C2: Dict[FrozenSet[int], float] | None = None,
    R_map: Dict[FrozenSet[int], List[int]] | None = None,
    D_all:  np.ndarray | None = None,
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
    Hybrid candidate generation for outlier detection.
    - Method A: Peripheral clusters
    - Method B: Marginal blocks
    - Method C: Beam expansion
    - Method U: Union-based expansion of promising subsets
    - Final fallback: full-set evaluation (S = R)

    Parameters
    ----------
    D : Distance matrix used for cost evaluation.
        - Non-structured: address-to-address distance matrix.
        - Structured: outer (unit-to-unit) distance matrix.
    R : Full list of GLOBAL address indices.
    R_seq : Route sequence used for heuristic generation.
    p : Postboxes / demand per address.
    E : Average unit revenue (scalar) or per-address unit revenues.
    APR : Distance cost per unit length.
    z : Candidate threshold for coverage improvement C2(S).
    strict_order : 
        If True, evaluate Type-1 (fixed order) routing.
        If False, allow Type-2 re-optimization.
    L_R : Length of the original route.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
    deterministic : Enforce deterministic solver behavior.
    solver : Solver backend used for route optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    methods : Hybrid methods to apply.
    A_kwargs : Parameters for Method A (peripheral clusters).
    B_kwargs : Parameters for Method B (marginal blocks).
    U_kwargs : Parameters for Method U (union-based subset expansion).
    precheck : If True, apply Type-1 precheck pruning before full evaluation.
    k_all : Maximum subset size handled exhaustively in Phase 1.
    k_max : Maximum subset size considered in beam expansion.
    B : Beam width.
    C_distance : Mapping S → distance change ΔL(S).
    C2 : Mapping S → coverage change C2(S).
    R_map : Mapping S → resulting route (only if precheck=True).
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
    # ------------------------------------------------------------
    # Ensure caches exist (used only for full evaluation)
    # ------------------------------------------------------------
    if inner_cache is None:
        inner_cache = {}
    if outer_cache is None:
        outer_cache = {}
    D_cluster = D_all if problem_type in STRUCTURED_PROBLEM_TYPES_SET else D

    # ============================================================
    # PHASE 2A: METHOD A — Peripheral clusters
    # ============================================================
    if "A" in methods:
        clusters_A = greedy_peripheral_clusters(
            D=D_cluster,
            R=R_seq,
            **A_kwargs,
        )
        for S in tqdm(clusters_A, desc="Method A clusters", leave=False):
            if S in C2:
                continue

            (
                C_distance,
                C2,
                R_map,
                inner_cache,
                outer_cache,
            ) = evaluate_subset(
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
    # ============================================================
    # PHASE 2B: METHOD B — Marginal blocks
    # ============================================================
    if "B" in methods:
        clusters_B = find_marginal_blocks(
            D=D_cluster,
            p=p,
            E=E,
            APR=APR,
            z=z,
            R=R_seq,
            L_u=L_u,
            **B_kwargs,
        )
        for S in tqdm(clusters_B, desc="Method B clusters", leave=False):
            if S in C2:
                continue
            (   C_distance,
                C2,
                R_map,
                inner_cache,
                outer_cache,
            ) = evaluate_subset(
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
    # ============================================================
    # PHASE 2C: BEAM EXPANSION
    # ============================================================
    if "Beam" in methods:
        (
            C_distance,
            C2,
            R_map,
            inner_cache,
            outer_cache,
        ) = beam_expand(
            D=D,
            R=R,
            p=p,
            E=E,
            APR=APR,
            z=z,
            C_distance=C_distance,
            C2=C2,
            R_map=R_map,
            strict_order=strict_order,
            precheck=precheck,
            deterministic=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            k_all=k_all,
            k_max=k_max,
            B=B,
            L_R=L_R,
            L_u=L_u,
            problem_type=problem_type,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
    # ============================================================
    # PHASE 2D: METHOD U — Union of promising subsets
    # ============================================================
    if "U" in methods:
        (
            C_distance,
            C2,
            R_map,
            inner_cache,
            outer_cache,
        ) = run_union_candidate_generation(
            D=D,
            R=R,
            p=p,
            E=E,
            APR=APR,
            z=z,
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
            U_kwargs=U_kwargs,
            C_distance=C_distance,
            C2=C2,
            R_map=R_map,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
    # ============================================================
    # PHASE 3: Ensure full-set evaluation exists
    # ============================================================
    S_full = frozenset(R)
    if S_full not in C2:
        (   C_distance,
            C2,
            R_map,
            inner_cache,
            outer_cache,
        ) = evaluate_subset(
            S=S_full,
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
