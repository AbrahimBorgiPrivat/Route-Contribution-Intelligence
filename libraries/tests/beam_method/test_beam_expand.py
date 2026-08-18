import numbers
import numpy as np
from typing import List

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.route_solver_structured import solve_structured_route
from libraries.utils.algorithm.single_route.coverage_cost import compute_coverage_change
from libraries.utils.algorithm.single_route.route_costs import compute_cost_change
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data
from libraries.utils.algorithm.structural_heuristics.beam_method import beam_expand

def _run_beam_case(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n: int = 20,
    solver: str = "ortools",
    E: float | List[float] | np.ndarray = 5.0,
    L_u: float | List[float] | None = None,
    ):
    print("\n====================================================")
    print(f"TEST BEAM EXPANSION: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print(f"  E-type={type(E).__name__}")
    print("====================================================")
    # --------------------------------------------------
    # Simulate instance
    # --------------------------------------------------
    D, p = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.0,
        outlier_fraction=0.05,
    )
    R = list(range(n))
    L_u_used = L_u if L_u is not None else 0.0
    # --------------------------------------------------
    # Baseline route
    # --------------------------------------------------
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
    # --------------------------------------------------
    # Phase 1: evaluate |S| = 1
    # --------------------------------------------------
    C_distance = {}
    C2 = {}
    R_map = {}
    APR = 0.05
    z = 0.0
    for i in R:
        S = frozenset({i})
        C_pre, R_s_pre = compute_cost_change(
            D=D,
            R=R,
            S=S,
            strict_order=strict_order,
            L_R=L_R,
            L_u=L_u_used,
            problem_type=problem_type,
            deterministic=True,
            solver=solver,
            ortools_time_limit=3,
            include_path=True,
        )
        C_distance[S] = C_pre
        C2[S] = compute_coverage_change(E, APR, p, R, S, C_pre)
        R_map[S] = R_s_pre
    # --------------------------------------------------
    # Run beam expansion
    # --------------------------------------------------
    (
        C_distance_final,
        C2_final,
        R_map_final,
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
        precheck=True,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        k_all=1,
        k_max=4,
        B=10,
        L_R=L_R,
        L_u=L_u_used,
        problem_type=problem_type,
    )
    # --------------------------------------------------
    # Validation
    # --------------------------------------------------
    assert isinstance(C_distance_final, dict)
    assert isinstance(C2_final, dict)
    assert isinstance(R_map_final, dict)
    for S in C2_final:
        assert isinstance(S, frozenset)
        assert S in C_distance_final
    for v in C2_final.values():
        assert isinstance(v, numbers.Real)
    for d in C_distance_final.values():
        assert isinstance(d, numbers.Real)
    for i in R:
        assert frozenset({i}) in C2_final
    if not strict_order:
        assert any(len(S) > 1 for S in C2_final)
    assert inner_cache in ({}, None)
    assert outer_cache in ({}, None)

def _run_beam_case_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    APR = 0.5,
    n_units: int = 4,
    solver: str = "ortools",
    E: float | List[float] | np.ndarray = 5.0,
    ):
    print("\n====================================================")
    print(f"TEST BEAM EXPANSION (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print(f"  E-type={type(E).__name__}")
    print("====================================================")
    # --------------------------------------------------
    # Simulate structured instance
    # --------------------------------------------------
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2024,
        asymmetry_strength=0.0,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    n = len(R)
    if isinstance(E, list):
        if len(E) == 1:
            E = E * n
        else:
            assert len(E) == n
    # --------------------------------------------------
    # Baseline structured route
    # --------------------------------------------------
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
    # --------------------------------------------------
    # Phase 1: evaluate |S| = 1
    # --------------------------------------------------
    C_distance = {}
    C2 = {}
    R_map = {}
    z = 0.0
    for i in R:
        S = frozenset({i})
        delta, R_s_pre, inner_cache, outer_cache = compute_cost_change(
            D=D_outer,
            R=R,
            S=S,
            strict_order=strict_order,
            L_R=L_R,
            problem_type=problem_type,
            deterministic=True,
            solver=solver,
            ortools_time_limit=3,
            include_path=True,
            D_all=D_all,
            inner_models=inner_models,
            inner_cache=inner_cache,
            outer_cache=outer_cache,
        )
        C_distance[S] = delta
        C2[S] = compute_coverage_change(E, APR, p, R, S, delta)
        R_map[S] = R_s_pre
    # --------------------------------------------------
    # Run beam expansion
    # --------------------------------------------------
    (
        C_distance_final,
        C2_final,
        R_map_final,
        inner_cache,
        outer_cache,
    ) = beam_expand(
        D=D_outer,
        R=R,
        p=p,
        E=E,
        APR=APR,
        z=z,
        C_distance=C_distance,
        C2=C2,
        R_map=R_map,
        strict_order=strict_order,
        precheck=True,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        k_all=1,
        k_max=10,
        B=10,
        L_R=L_R,
        problem_type=problem_type,
        D_all=D_all,
        inner_models=inner_models,
        inner_cache=inner_cache,
        outer_cache=outer_cache,
    )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------
    assert isinstance(C_distance_final, dict)
    assert isinstance(C2_final, dict)
    assert isinstance(R_map_final, dict)
    for S in C2_final:
        assert isinstance(S, frozenset)
        assert S in C_distance_final
    for v in C2_final.values():
        assert isinstance(v, numbers.Real)
    for d in C_distance_final.values():
        assert isinstance(d, numbers.Real)
    for i in R:
        assert frozenset({i}) in C2_final
    if not strict_order:
        assert any(len(S) > 1 for S in C2_final)
    assert isinstance(inner_cache, dict)
    assert isinstance(outer_cache, dict)

def test_beam_unstructured():
    _run_beam_case(
        label="Type 1 — TSP — scalar E",
        strict_order=True,
        problem_type="TSP",
        E=5.0,
    )
    _run_beam_case(
        label="Type 2 — TSP — scalar E",
        strict_order=False,
        problem_type="TSP",
        E=5.0,
    )

    n = 20
    rng = np.random.default_rng(42)

    E_vec = rng.uniform(3.0, 7.0, size=n)
    _run_beam_case(
        label="Type 1 — TSP — vector E",
        strict_order=True,
        problem_type="TSP",
        E=E_vec,
    )
    _run_beam_case(
        label="Type 2 — TSP — vector E",
        strict_order=False,
        problem_type="TSP",
        E=E_vec,
    )

    L_u_vec = rng.uniform(0.5, 2.0, size=n)
    _run_beam_case(
        label="Type 2 — HPP — greedy — vector L_u",
        strict_order=False,
        problem_type="HPP",
        solver="greedy_denn",
        E=5.0,
        L_u=L_u_vec,
    )


def test_beam_structured():
    _run_beam_case_structured(
        label="OUT:HPP — Type 1 — scalar E",
        strict_order=True,
        problem_type="OUT:HPP",
        solver="ortools",
        E=5.0,
    )

    _run_beam_case_structured(
        label="OUT:HPP — Type 2 — greedy — scalar E",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        E=5.0,
        APR = 5,
    )

    _run_beam_case_structured(
        label="OUT:TSP — Type 1 — scalar E",
        strict_order=True,
        problem_type="OUT:TSP",
        solver="ortools",
        E=5.0,
        APR = 5,
    )

    _run_beam_case_structured(
        label="OUT:TSP — Type 2 — greedy — vector E",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="greedy",
        E=[5.0],  
        APR = 5,
    )

if __name__ == "__main__":
    test_beam_unstructured()
    test_beam_structured()