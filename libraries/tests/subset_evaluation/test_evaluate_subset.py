import numbers
import numpy as np
from typing import List

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.route_solver_structured import solve_structured_route
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data
from libraries.utils.algorithm.structural_heuristics.subset_evaluation import evaluate_subset

def _run_subset_case_non_structured(
    label: str,
    strict_order: bool,
    problem_type: str,
    precheck: bool,
    *,
    n: int = 10,
    solver: str = "ortools",
    L_u: float | List[float] | None = None,
    ):
    print("\n====================================================")
    print(f"TEST EVALUATE_SUBSET (NON-STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  precheck={precheck}")
    print("====================================================")
    D, p = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.1,
        outlier_fraction=0.1,
    )
    R = list(range(n))
    S = frozenset({0, 1})
    E = 5.0
    APR = 0.05
    L_u_used = L_u if L_u is not None else 0.0
    _, L_R = solve_route(
        D=D,
        R=R,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        L_u=L_u_used,
        deterministic=True,
        ortools_time_limit=3,
    )
    C_distance = {}
    C2 = {}
    R_map = {}
    C_distance, C2, R_map, inner_cache, outer_cache = evaluate_subset(
        S=S,
        D=D,
        R=R,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        L_R=L_R,
        L_u=L_u_used,
        problem_type=problem_type,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        fixed_endpoints=None,
        initial_point_method=None,
        precheck=precheck,
        C_distance=C_distance,
        C2=C2,
        R_map=R_map,
    )

    assert isinstance(C_distance, dict)
    assert isinstance(C2, dict)
    assert S in C_distance
    assert S in C2
    assert isinstance(C_distance[S], numbers.Real)
    assert isinstance(C2[S], numbers.Real)
    if precheck:
        assert S in R_map
        assert isinstance(R_map[S], list)
    else:
        assert S not in R_map
    assert inner_cache in (None, {})
    assert outer_cache in (None, {})


def test_evaluate_subset_non_structured():
    _run_subset_case_non_structured(
        label="Type 1 — TSP — precheck",
        strict_order=True,
        problem_type="TSP",
        precheck=True,
    )
    _run_subset_case_non_structured(
        label="Type 2 — TSP — no precheck",
        strict_order=False,
        problem_type="TSP",
        precheck=False,
    )
    _run_subset_case_non_structured(
        label="Type 2 — HPP — greedy + L_u",
        strict_order=False,
        problem_type="HPP",
        solver="greedy_denn",
        L_u=[1.0] * 10,
        precheck=True,
    )

def _run_subset_case_structured(
    label: str,
    strict_order: bool,
    problem_type: str,
    precheck: bool,
    *,
    n_units: int = 4,
    solver: str = "ortools",
):
    print("\n====================================================")
    print(f"TEST EVALUATE_SUBSET (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  precheck={precheck}")
    print("====================================================")
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2024,
        asymmetry_strength=0.1,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    S = frozenset({R[0]})
    E = 5.0
    APR = 0.05
    _, L_R, inner_cache, outer_cache = solve_structured_route(
        D_outer=D_outer,
        D_all=D_all,
        R=R,
        inner_models=inner_models,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        deterministic=True,
        ortools_time_limit=3,
    )
    C_distance = {}
    C2 = {}
    R_map = {}
    C_distance, C2, R_map, inner_cache, outer_cache = evaluate_subset(
        S=S,
        D=D_outer,
        R=R,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        L_R=L_R,
        L_u=0.0,
        problem_type=problem_type,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        fixed_endpoints=None,
        initial_point_method=None,
        precheck=precheck,
        C_distance=C_distance,
        C2=C2,
        R_map=R_map,
        D_all=D_all,
        inner_models=inner_models,
        inner_cache=inner_cache,
        outer_cache=outer_cache,
    )
    assert S in C_distance
    assert S in C2
    assert isinstance(C_distance[S], numbers.Real)
    assert isinstance(C2[S], numbers.Real)
    if precheck:
        assert S in R_map
        assert isinstance(R_map[S], list)
    assert isinstance(inner_cache, dict)
    assert isinstance(outer_cache, dict)

def test_evaluate_subset_structured():
    _run_subset_case_structured(
        label="OUT:HPP — Type 1 — precheck",
        strict_order=True,
        problem_type="OUT:HPP",
        precheck=True,
    )
    _run_subset_case_structured(
        label="OUT:HPP — Type 2 — greedy",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        precheck=False,
    )
    _run_subset_case_structured(
        label="OUT:TSP — Type 2 — greedy — precheck",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="greedy",
        precheck=True,
    )

if __name__ == "__main__":
    test_evaluate_subset_non_structured()
    test_evaluate_subset_structured()
