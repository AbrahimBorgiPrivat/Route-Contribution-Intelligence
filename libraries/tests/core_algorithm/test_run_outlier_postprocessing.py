import numbers
import numpy as np
from typing import Dict, Any, List, Optional

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.core_algorithm import (
    run_outlier_postprocessing,
)
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.structured_route_builder import (
    build_structured_route_data,
)
from libraries.utils.algorithm.structural_heuristics.full_evaluation import full_set_evaluation

def _prepare_exact_unstructured(
    *,
    n: int,
    E,
    APR: float,
    strict_order: bool,
    problem_type: str,
    ):
    D, p = simulate_addresses(
        n=n,
        seed=2719,
        asymmetry_strength=0.1,
        cluster_strength=0.5,
        outlier_fraction=0.1,
    )
    R = list(range(n))
    R_seq, L_R = solve_route(
        D=D,
        R=R,
        strict_order=strict_order,
        problem_type=problem_type,
        L_u=0.0,
        deterministic=True,
        solver="greedy",
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
        L_u=0.0,
        problem_type=problem_type,
        deterministic=True,
        precheck=False,
        solver="greedy",
    )
    return dict(
        D=D,
        p=p,
        R=R,
        R_seq=R_seq,
        L_R=L_R,
        C_distance=C_distance,
        C2=C2,
    )

def _prepare_exact_structured(
    *,
    n_units: int,
    E,
    APR: float,
    strict_order: bool,
    problem_type: str,
    ):
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2719,
        asymmetry_strength=0.1,
        cluster_strength=0.5,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    _, _, inner_cache, outer_cache = solve_route = None, None, None, None
    _, _, inner_cache, outer_cache = None, None, None, None
    result = full_set_evaluation(
        D=D_outer,
        R=R,
        p=p,
        E=E,
        APR=APR,
        L_R=0.0,
        strict_order=strict_order,
        k_all=len(R),
        problem_type=problem_type,
        deterministic=True,
        precheck=False,
        solver="greedy",
        D_all=D_all,
        inner_models=inner_models,
    )
    C_distance, C2, inner_cache, outer_cache = result
    return dict(
        D=D_big,
        p=p,
        R=R,
        R_seq=R,
        L_R=0.0,
        C_distance=C_distance,
        C2=C2,
        D_outer=D_outer,
        D_all=D_all,
        inner_models=inner_models,
        inner_cache=inner_cache,
        outer_cache=outer_cache,
    )

# =========================================================
# TESTS — UNSTRUCTURED
# =========================================================

def test_run_outlier_postprocessing_unstructured():
    n = 10
    APR = 0.05
    z = 0.0
    prep = _prepare_exact_unstructured(
        n=n,
        E=5.0,
        APR=APR,
        strict_order=False,
        problem_type="TSP",
    )
    (result, C_distance_all) = run_outlier_postprocessing(
        **prep,
        E=5.0,
        APR=APR,
        z=z,
        L_u=0.0,
        strict_order=False,
        problem_type="TSP",
        solver="greedy",
        deterministic=True,
        ortools_time_limit=2,
        fixed_endpoints=None,
        initial_point_method=None,
        return_c_distance=True,
    )
    (   coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_best,
        C2_max,
        DG_R,
        DG_best,
    ) = result
    # -------------------------
    # Invariants
    # -------------------------
    assert isinstance(coverage_change, dict)
    assert isinstance(C_distance_outliers, dict)
    assert isinstance(C_distance_all, dict)
    assert isinstance(R_original, list)
    assert isinstance(R_star, list)
    assert isinstance(L_original, numbers.Real)
    assert isinstance(L_opt, numbers.Real)
    assert isinstance(C2_max, numbers.Real)
    assert isinstance(DG_R, numbers.Real)
    assert isinstance(DG_best, numbers.Real)
    assert DG_best >= DG_R
    assert set(R_star) == set(R_original) - set(S_best)
    for S, v in coverage_change.items():
        assert isinstance(S, frozenset)
        assert isinstance(v, numbers.Real)
        assert S in C_distance_outliers


# =========================================================
# TESTS — STRUCTURED
# =========================================================

def test_run_outlier_postprocessing_structured():
    APR = 0.75
    z = 0.0
    prep = _prepare_exact_structured(
        n_units=4,
        E=5.0,
        APR=APR,
        strict_order=False,
        problem_type="OUT:HPP",
    )
    result = run_outlier_postprocessing(
        C2=prep["C2"],
        C_distance=prep["C_distance"],
        R=prep["R"],
        R_seq=prep["R_seq"],
        L_R=prep["L_R"],
        D=prep["D"],
        p=prep["p"],
        E=5.0,
        APR=APR,
        z=z,
        L_u=0.0,
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        deterministic=True,
        ortools_time_limit=2,
        fixed_endpoints=None,
        initial_point_method=None,
        D_outer=prep["D_outer"],
        D_all=prep["D_all"],
        inner_models=prep["inner_models"],
        inner_cache=prep["inner_cache"],
        outer_cache=prep["outer_cache"],
    )
    (
        coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_best,
        C2_max,
        DG_R,
        DG_best,
    ) = result

    # -------------------------
    # Structured invariants
    # -------------------------
    assert isinstance(coverage_change, dict)
    assert isinstance(R_original, list)
    assert isinstance(R_star, list)
    assert isinstance(C_distance_outliers, dict)
    assert isinstance(L_original, numbers.Real)
    assert isinstance(L_opt, numbers.Real)
    assert isinstance(C2_max, numbers.Real)
    assert DG_best >= DG_R
    assert set(R_star) == set(R_original) - set(S_best)
    assert all(isinstance(i, int) for i in R_star)

def test_run_outlier_postprocessing_structured_recompute_C2():
    APR = 0.75
    z = 0.0

    prep = _prepare_exact_structured(
        n_units=4,
        E=5.0,
        APR=APR,
        strict_order=False,
        problem_type="OUT:HPP",
    )

    # -------------------------------------------------
    # Pass C2=None to trigger recomputation
    # -------------------------------------------------
    result = run_outlier_postprocessing(
        C2=None,  # <-- critical change
        C_distance=prep["C_distance"],
        R=prep["R"],
        R_seq=prep["R_seq"],
        L_R=prep["L_R"],
        D=prep["D"],
        p=prep["p"],
        E=5.0,
        APR=APR,
        z=z,
        L_u=0.0,
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        deterministic=True,
        ortools_time_limit=2,
        fixed_endpoints=None,
        initial_point_method=None,
        D_outer=prep["D_outer"],
        D_all=prep["D_all"],
        inner_models=prep["inner_models"],
        inner_cache=prep["inner_cache"],
        outer_cache=prep["outer_cache"],
    )

    (
        coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_best,
        C2_max,
        DG_R,
        DG_best,
    ) = result

    # -------------------------
    # Structured invariants
    # -------------------------
    assert isinstance(coverage_change, dict)
    assert isinstance(R_original, list)
    assert isinstance(R_star, list)
    assert isinstance(C_distance_outliers, dict)
    assert isinstance(L_original, numbers.Real)
    assert isinstance(L_opt, numbers.Real)
    assert isinstance(C2_max, numbers.Real)
    assert DG_best >= DG_R
    assert set(R_star) == set(R_original) - set(S_best)
    assert all(isinstance(i, int) for i in R_star)
    assert isinstance(C2_max, numbers.Real)

if __name__ == "__main__":
    test_run_outlier_postprocessing_unstructured()
    test_run_outlier_postprocessing_structured()
    test_run_outlier_postprocessing_structured_recompute_C2()
