import numpy as np
from typing import List, Dict, Tuple, FrozenSet,Optional

from libraries.config import HYBRID_METHODS

from libraries.utils.algorithm.single_route.outlier_detection import detect_outliers
from libraries.utils.algorithm.single_route.coverage_cost import compute_coverage_change
from libraries.utils.algorithm.single_route.coverage_cost import compute_rute_covarage
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.route_solver_structured import solve_structured_route, apply_s_to_structured_model
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data
from libraries.utils.algorithm.structural_heuristics.full_evaluation import full_set_evaluation
from libraries.utils.algorithm.structural_heuristics.hybrid_candidate_generation import run_hybrid_candidate_generation
from libraries.config import PROBLEM_TYPES, SOLVERS, STRUCTURED_PROBLEM_TYPES_SET, HYBRID_METHODS_LIST, HPP_SOLVERS


def run_outlier_postprocessing(
    C2: Optional[Dict[FrozenSet[int], float]],
    C_distance: Dict[FrozenSet[int], float],
    R: List[int],
    R_seq: List[int],
    L_R: float,
    D: np.ndarray,
    p: List[float],
    E: float | List[float] | np.ndarray,
    APR: float,
    z: float,
    L_u: float | List[float] | np.ndarray,
    strict_order: bool,
    problem_type: PROBLEM_TYPES,
    solver: SOLVERS,
    deterministic: bool,
    ortools_time_limit: int,
    fixed_endpoints: Dict[str, int | None] | None,
    initial_point_method: Dict | None,
    *,
    D_outer=None,
    D_all=None,
    inner_models=None,
    inner_solver=None,
    inner_cache=None,
    outer_cache=None,
    return_c_distance: bool = False,
    ):
    """
    Shared post-processing for exact and hybrid outlier detection.

    Includes:
    - Phase 3: Detect significant outliers
    - Phase 4: Construct final route + optimized length
    - Final coverage computation

    Returns identical tuple structure as original functions.
    """

    # ---------------------------------------------------------
    # RECOMPUTE C2 IF NOT PROVIDED
    # ---------------------------------------------------------
    if C2 is None:
        C2 = {}
        for S, C_value in C_distance.items():
            C2[S] = compute_coverage_change(
                E=E,
                APR=APR,
                p=p,
                R=R,
                S=set(S),
                C=C_value
            )
    S_full = frozenset(R)
    if S_full not in C2:
        C2[S_full] = 0.0

    # ---------------------------------------------------------
    # PHASE 3: DETECT SIGNIFICANT OUTLIERS
    # ---------------------------------------------------------
    S_sig, coverage_change = detect_outliers(C2, z)
    C_distance_outliers = {S: C_distance[S] for S in S_sig}

    if len(S_sig) > 0:
        S_best_outlier = max(S_sig, key=lambda S: C2[S])
        R_star = [i for i in R if i not in S_best_outlier]
        C2_max = C2[S_best_outlier]
    else:
        S_best_outlier = frozenset()
        R_star = list(R)
        C2_max = C2.get(frozenset(R), 0.0)

    # ---------------------------------------------------------
    # PHASE 4: CONSTRUCT FINAL ROUTE + LENGTH
    # ---------------------------------------------------------
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        (
            D_outer_new,
            D_all_new,
            R_local_reduced,
            inner_models_new,
            _,
            address_index_map,
        ) = apply_s_to_structured_model(
            D_outer=D_outer,
            D_all=D_all,
            R=R_star,
            inner_models=inner_models,
            S=S_best_outlier,
        )

        R_seq_local, L_opt, _, _ = solve_structured_route(
            D_outer=D_outer_new,
            D_all=D_all_new,
            R=R_local_reduced,
            inner_models=inner_models_new,
            strict_order=strict_order,
            problem_type=problem_type,
            L_u=L_u,
            deterministic=deterministic,
            solver=solver,
            inner_solver=inner_solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )

        inv_address_index_map = {v: k for k, v in address_index_map.items()}
        R_star = [inv_address_index_map[i] for i in R_seq_local]

    else:
        if not strict_order:
            if len(S_sig) == 0:
                R_star = R_seq
                L_opt = L_R
            else:
                R_star, L_opt = solve_route(
                    D=D[np.ix_(R_star, R_star)],
                    R=R_star,
                    strict_order=False,
                    problem_type=problem_type,
                    L_u=L_u,
                    deterministic=deterministic,
                    solver=solver,
                    ortools_time_limit=ortools_time_limit,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                )
        else:
            _, L_opt = solve_route(
                D=D,
                R=R_star,
                strict_order=True,
                problem_type=problem_type,
                L_u=L_u,
            )

    # ---------------------------------------------------------
    # FINAL COVERAGE
    # ---------------------------------------------------------
    DG_R = compute_rute_covarage(
        E=E,
        APR=APR,
        p=p,
        L_R=L_R,
        L_u=L_u,
    )
    DG_best = DG_R + C2_max if len(S_sig) > 0 else DG_R
    result = (
        coverage_change,
        C_distance_outliers,
        R_seq,
        R_star,
        L_R,
        L_opt,
        S_best_outlier,
        C2_max if C2_max >= 0 else 0,
        DG_R,
        DG_best,
    )
    if return_c_distance:
        cache_payload = {
            "C_distance_full": C_distance,
            "D_outer": D_outer,
            "D_all": D_all,
            "inner_models": inner_models,
            "inner_solver": inner_solver,
            "inner_cache": inner_cache,
            "outer_cache": outer_cache,
        }
        return result, cache_payload
    return result

def find_outliers(
    D: np.ndarray,
    p: List[float],
    E: float | List[float] | np.ndarray,
    APR: float,
    strict_order: bool,
    z: float,
    *,
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    inner_solver: Optional[HPP_SOLVERS] =  None,
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    nodes: List[Dict] | None = None,
    return_c_distance: bool = False,
    ) -> Tuple:
    """
    Exact outlier detection for route optimization.

    Evaluates all possible address removal subsets S ⊆ R and identifies those
    whose removal yields significant coverage improvement. This function performs
    a complete exhaustive search and serves as the theoretical reference against
    which the hybrid method is compared.

    ----------
    Parameters
    ----------
    D : Distance matrix used for routing and cost evaluation.
        - Non-structured: address-to-address distance matrix.
        - Structured: full node distance matrix (used to derive structured models).
    p : Demand / postboxes per address.
    E : Unit revenue.
        - Scalar: average unit revenue.
        - Vector: per-address unit revenue.
    APR : Distance cost per unit length.
    strict_order : Routing mode selector.
        - True: fixed-order evaluation (Type 1).
        - False: allow re-optimization (Type 2).
    z : Threshold for significant coverage improvement.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
        - "TSP", "HPP" for non-structured routing.
        - "OUT:TSP", "OUT:HPP" for structured routing.
    deterministic : Enforce deterministic solver behavior.
    solver : Solver backend used for route optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    nodes : Structured node descriptions.
        - Required for OUT:TSP / OUT:HPP.

    -------
    Returns
    -------
    coverage_change : Mapping from significant subsets S to coverage change C2(S).
    C_distance_outliers : Mapping from significant subsets S to distance change ΔL(S).
    R_original : Original route sequence.
    R_star : Optimized route after outlier removal.
    L_R : Length of the original route.
    L_opt : Length of the optimized route.
    S_best_outlier : Subset with maximum coverage improvement.
    C2_max : Maximum coverage improvement achieved.
    DG_R : Coverage of the original route.
    DG_best : Coverage of the optimized route.
    """
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        # ------------------------------
        # Structured case
        # ------------------------------
        if nodes is None:
            raise ValueError(
                "nodes must be provided for structured problem types (OUT:TSP / OUT:HPP)"
            )
        if inner_solver is None:
            print("Inner HPP solver for Structured hybrid method is not declared. Setting default inner_solver = 'ortools'")
            inner_solver = "ortools"
        n = len(p)
        R = list(range(n))
        D_outer, inner_models, D_all = build_structured_route_data(
            D_big=D,
            nodes=nodes,
        )
        R_seq, L_R, inner_cache, outer_cache = solve_structured_route(
            D_outer=D_outer,
            D_all=D_all,
            R=list(R),
            inner_models=inner_models,
            strict_order=strict_order,
            problem_type=problem_type,
            solver=solver,
            inner_solver=inner_solver,
            deterministic=deterministic,
            ortools_time_limit=ortools_time_limit
        )
        result = full_set_evaluation(
            D=D_outer,
            R=R,
            p=p,
            E=E,
            APR=APR,
            L_R=L_R,
            strict_order=strict_order,
            k_all=n,  
            problem_type=problem_type,
            deterministic=deterministic,
            precheck=False,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
        C_distance, C2, inner_cache, outer_cache = result
    else:
        # ------------------------------
        # Non-structured case
        # ------------------------------
        n = len(p)
        R = list(range(n))
        R_seq, L_R = solve_route(
            D=D,
            R=R,
            strict_order=strict_order,
            problem_type=problem_type,
            L_u=L_u,
            deterministic=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
        )
        C_distance, C2 = full_set_evaluation(
            D=D,
            R=R,
            p=p,
            E=E,
            APR=APR,
            L_R=L_R,
            strict_order=strict_order,
            k_all=n,  
            L_u=L_u,
            problem_type=problem_type,
            deterministic=deterministic,
            precheck=False,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
        )
    # ---------------------------------------------------------
    # RUN PHASE 3 + 4 POST-PROCESSING
    # ---------------------------------------------------------
    result = run_outlier_postprocessing(
        C2=C2,
        C_distance=C_distance,
        R=R,
        R_seq=R_seq,
        L_R=L_R,
        D=D,
        p=p,
        E=E,
        APR=APR,
        z=z,
        L_u=L_u,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        deterministic=deterministic,
        ortools_time_limit=ortools_time_limit,
        fixed_endpoints=fixed_endpoints,
        initial_point_method=initial_point_method,
        D_outer=D_outer if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        D_all=D_all if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        inner_models=inner_models if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        inner_solver=inner_solver,
        return_c_distance=return_c_distance,
    )
    return result

def find_outliers_hybrid(
    D: np.ndarray,
    p: List[float],
    E: float | List[float] | np.ndarray,
    APR: float,
    strict_order: bool,
    z: float,
    *,
    R: List[int] | None = None,
    k_all: int = 1,
    k_max: int = 50,
    B: int = 100,
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    deterministic: bool = True,
    precheck: bool = False,
    solver: SOLVERS = "ortools",
    inner_solver:  Optional[HPP_SOLVERS] =  None,
    ortools_time_limit: int = 2,
    fixed_endpoints: Dict[str, int | None] | None = None,
    initial_point_method: Dict | None = None,
    methods: List[HYBRID_METHODS] | None = None,
    A_kwargs: Dict | None = None,
    B_kwargs: Dict | None = None,
    U_kwargs: Dict | None = None,
    nodes: List[Dict] | None = None,
    return_c_distance: bool = False,
    ) -> Tuple:
    """
    Hybrid outlier detection for route optimization.

    The algorithm proceeds in four phases:
    - Phase 1: Full evaluation of all subsets |S| ≤ k_all
    - Phase 2: Hybrid candidate generation
        * Method A: Peripheral clusters
        * Method B: Marginal blocks
        * Method C: Beam expansion
        * Method D: Union expansion
    - Phase 3: Outlier detection based on C2(S)
    - Phase 4: Construction of the final optimized route

    ----------
    Parameters
    ----------
    D : Distance matrix used for routing and cost evaluation.
        - Non-structured: address-to-address distance matrix.
        - Structured: full node distance matrix (used to derive structured models).
    p : Demand / postboxes per address.
    E : Unit revenue.
        - Scalar: average unit revenue.
        - Vector: per-address unit revenue.
    APR : Distance cost per unit length.
    strict_order : Routing mode selector.
        - True: fixed-order evaluation (Type 1).
        - False: allow re-optimization (Type 2).
    z : Threshold for significant coverage improvement.
    R : Initial route as GLOBAL address indices.
        - If None, defaults to range(len(p)).
    k_all : Maximum subset size evaluated exhaustively in Phase 1.
    k_max : Maximum subset size considered by hybrid expansion.
    B : Beam width used in beam expansion.
    L_u : Internal per-address cost(s).
    problem_type : Routing problem type.
        - "TSP", "HPP" for non-structured routing.
        - "OUT:TSP", "OUT:HPP" for structured routing.
    deterministic : Enforce deterministic solver behavior.
    precheck : Enable Type-1 precheck pruning in hybrid phases.
    solver : Solver backend used for route optimization.
    ortools_time_limit : Time limit for OR-Tools solvers.
    fixed_endpoints : Optional fixed endpoints for HPP variants.
    initial_point_method : Optional solver initialization method.
    methods : Hybrid methods to apply.
        - "A": Peripheral clusters
        - "B": Marginal blocks
        - "Beam": Beam expansion
    A_kwargs : Parameters for Method A.
    B_kwargs : Parameters for Method B.
    nodes : Structured node descriptions (required for OUT:* problems).

    -------
    Returns
    -------
    coverage_change : Mapping from significant subsets S to coverage change C2(S).
    C_distance_outliers : Mapping from significant subsets S to distance change ΔL(S).
    R_original : Original route sequence.
    R_star : Optimized route after outlier removal.
    L_R : Length of the original route.
    L_opt : Length of the optimized route.
    S_best_outlier : Subset with maximum coverage improvement.
    C2_max : Maximum coverage improvement achieved.
    DG_R : Coverage of the original route.
    DG_best : Coverage of the optimized route.
    """
    if methods is None:
        methods = HYBRID_METHODS_LIST
    if A_kwargs is None:
        A_kwargs = {}
    if B_kwargs is None:
        B_kwargs = {}
    if U_kwargs is None:
        U_kwargs = {}

    n = len(p)
    if R is None:
        R = list(range(n))
    C2: Dict[FrozenSet[int], float] = {}
    C_distance: Dict[FrozenSet[int], float] = {}
    R_map: Dict[FrozenSet[int], List[int]] = {}
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        # ============================================================
        # ROUTE INITIALIZATION + STRUCTURED MODEL BUILDING 
        # ============================================================
        if nodes is None:
            raise ValueError("nodes must be provided for structured problem types (OUT:TSP / OUT:HPP)")
        if inner_solver is None:
            print("Inner HPP solver for Structured hybrid method is not declared. Setting default inner_solver = 'ortools'")
            inner_solver = "ortools"
        D_outer, inner_models, D_all = build_structured_route_data(
            D_big=D,
            nodes=nodes,
        )
        R_seq, L_R, inner_cache, outer_cache = solve_structured_route(
            D_outer=D_outer,
            D_all=D_all,
            R=list(R),
            inner_models=inner_models,
            strict_order=strict_order,
            problem_type=problem_type,
            solver=solver,
            inner_solver = inner_solver,
            deterministic=deterministic,
            ortools_time_limit=ortools_time_limit,
        )
        # ============================================================
        # PHASE 1 (small-set exhaustive)
        # ============================================================    
        result = full_set_evaluation(
            D=D_outer,
            R=R,
            p=p,
            E=E,
            APR=APR,
            L_R=L_R,
            strict_order=strict_order,
            k_all=k_all,
            L_u=L_u,
            problem_type=problem_type,
            deterministic=deterministic,
            precheck=precheck,
            solver=solver,
            inner_solver=inner_solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
        if precheck:
            C_distance, C2, R_map, inner_cache, outer_cache = result
        else:
            C_distance, C2, inner_cache, outer_cache = result
            R_map = {}
        # ============================================================
        # PHASE 2 (hybrid candidate generation)
        # ============================================================
        C_distance, C2, R_map, inner_cache, outer_cache = run_hybrid_candidate_generation(
            D=D_outer,
            R=R,
            R_seq=R_seq,
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
            inner_solver=inner_solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            methods=methods,
            A_kwargs=A_kwargs,
            B_kwargs=B_kwargs,
            U_kwargs=U_kwargs,
            precheck=precheck,
            k_all=k_all,
            k_max=k_max,
            B=B,
            C_distance=C_distance,
            C2=C2,
            R_map=R_map,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
    else:
        # ============================================================
        # ROUTE INITIALIZATION 
        # ============================================================
        R_seq, L_R = solve_route(
            D=D,
            R=R,
            strict_order=strict_order,
            problem_type=problem_type,
            L_u=L_u,
            deterministic=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
        )
        # ============================================================
        # PHASE 1 (small-set exhaustive)
        # ============================================================    
        result = full_set_evaluation(
            D=D,
            R=R,
            p=p,
            E=E,
            APR=APR,
            L_R=L_R,
            strict_order=strict_order,
            k_all=k_all,
            L_u=L_u,
            problem_type=problem_type,
            deterministic=deterministic,
            precheck=precheck,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
        )
        if precheck:
            C_distance, C2, R_map = result
        else:
            C_distance, C2 = result
            R_map = {}
        # ============================================================
        # PHASE 2 (hybrid candidate generation)
        # ============================================================    
        C_distance, C2, R_map, _, _ = run_hybrid_candidate_generation(
            D=D,
            R=R,
            R_seq=R_seq,
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
            methods=methods,
            A_kwargs=A_kwargs,
            B_kwargs=B_kwargs,
            U_kwargs=U_kwargs,
            precheck=precheck,
            k_all=k_all,
            k_max=k_max,
            B=B,
            C_distance=C_distance,
            C2=C2,
            R_map=R_map,
        )
    # ============================================================
    # PHASE 3 + 4 POST-PROCESSING + FINAL RESULT CONSTRUCTION
    # ============================================================
    result = run_outlier_postprocessing(
        C2=C2,
        C_distance=C_distance,
        R=R,
        R_seq=R_seq,
        L_R=L_R,
        D=D,
        p=p,
        E=E,
        APR=APR,
        z=z,
        L_u=L_u,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        deterministic=deterministic,
        ortools_time_limit=ortools_time_limit,
        fixed_endpoints=fixed_endpoints,
        initial_point_method=initial_point_method,
        D_outer=D_outer if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        D_all=D_all if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        inner_models=inner_models if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        inner_solver=inner_solver,
        inner_cache=inner_cache if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        outer_cache=outer_cache if problem_type in STRUCTURED_PROBLEM_TYPES_SET else None,
        return_c_distance=return_c_distance,
    )
    return result