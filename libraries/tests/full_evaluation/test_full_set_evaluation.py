import numbers
from typing import List

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data
from libraries.utils.algorithm.structural_heuristics.full_evaluation import full_set_evaluation


# =========================================================
# Non-structured test
# =========================================================

def _run_full_set_case(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    precheck: bool,
    n: int = 8,
    k_all: int = 2,
    solver: str = "ortools",
    L_u: float | List[float] | None = None,
    assert_full_enumeration: bool = False,
):
    print("\n====================================================")
    print(f"TEST FULL_SET_EVALUATION: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  precheck={precheck}")
    print(f"  n={n}, k_all={k_all}")
    print(f"  solver={solver}")
    print("====================================================")

    # --------------------------------------------------
    # Simulate data
    # --------------------------------------------------
    D, p = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.1,
        outlier_fraction=0.1,
    )
    R = list(range(n))
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
    # --------------------------------------------------
    # Run full set evaluation
    # --------------------------------------------------
    result = full_set_evaluation(
        D=D,
        R=R,
        p=p,
        E=5.0,
        APR=0.03,
        L_R=L_R,
        strict_order=strict_order,
        k_all=k_all,
        L_u=L_u_used,
        problem_type=problem_type,
        deterministic=True,
        precheck=precheck,
        solver=solver,
        ortools_time_limit=3,
    )
    # --------------------------------------------------
    # Unpack result
    # --------------------------------------------------
    if precheck:
        assert len(result) == 3
        C_distance, C2, R_map = result
    else:
        assert len(result) == 2
        C_distance, C2 = result
        R_map = None
    # --------------------------------------------------
    # Validate dictionaries
    # --------------------------------------------------
    assert isinstance(C_distance, dict)
    assert isinstance(C2, dict)
    assert set(C_distance.keys()) == set(C2.keys())
    for S, delta in C_distance.items():
        assert isinstance(S, frozenset)
        assert all(isinstance(i, int) for i in S)
        assert isinstance(delta, numbers.Real)
    for c2 in C2.values():
        assert isinstance(c2, numbers.Real)
    # --------------------------------------------------
    # Validate R_map if precheck
    # --------------------------------------------------
    if precheck:
        assert isinstance(R_map, dict)
        assert set(R_map.keys()) == set(C_distance.keys())
        for S, R_s in R_map.items():
            assert isinstance(R_s, list)
            assert set(R_s).issubset(set(R))
            assert not set(S).intersection(R_s)
    # --------------------------------------------------
    # Full enumeration check
    # --------------------------------------------------
    if assert_full_enumeration:
        expected = (2 ** n) - 1  # all non-empty subsets
        assert len(C_distance) == expected
        sizes_present = {len(S) for S in C_distance.keys()}
        assert sizes_present == set(range(1, n + 1))

# =========================================================
# Structured test 
# =========================================================
def _run_full_set_case_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n_units: int = 4,
    k_all: int = 2,
    solver: str = "ortools",
):
    print("\n====================================================")
    print(f"TEST FULL_SET_EVALUATION (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    # --------------------------------------------------
    # Simulate structured instance
    # --------------------------------------------------
    D_big, nodes, _ = simulate_structured_route(
        n_units=n_units,
        min_unit_size=3,
        max_unit_size=4,
        seed=2024,
        asymmetry_strength=0.1,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes"])
    n = len(R)

    # --------------------------------------------------
    # Run full set evaluation (structured)
    # --------------------------------------------------
    result = full_set_evaluation(
        D=D_outer,
        R=R,
        p=[1.0] * n,
        E=5.0,
        APR=0.3,
        L_R=None,
        strict_order=strict_order,
        k_all=min(k_all, n),
        problem_type=problem_type,
        deterministic=True,
        precheck=True,
        solver=solver,
        D_all=D_all,
        inner_models=inner_models,
    )

    # --------------------------------------------------
    # Unpack result
    # --------------------------------------------------
    C_distance, C2, R_map, inner_cache, outer_cache = result
    print(f"Number of evaluated removal sets: {len(C_distance)}")
    print(f"Number of cached inner solutions: {len(inner_cache)}")
    print(f"Number of cached outer solutions: {len(outer_cache)}")

    # --------------------------------------------------
    # Validate outputs
    # --------------------------------------------------
    assert isinstance(C_distance, dict)
    assert isinstance(C2, dict)
    assert isinstance(R_map, dict)
    for S, delta in C_distance.items():
        assert isinstance(S, frozenset)
        assert isinstance(delta, numbers.Real)
    for S, R_s in R_map.items():
        assert set(R_s).issubset(set(R))
        assert not set(S).intersection(R_s)

    # --------------------------------------------------
    # Cache expectations
    # --------------------------------------------------
    if strict_order:
        assert inner_cache == {}
        assert outer_cache == {}
    else:
        assert isinstance(inner_cache, dict)
        assert isinstance(outer_cache, dict)
        assert len(inner_cache) > 0
        assert len(outer_cache) > 0

def test_full_set_evaluation_non_structured():
    _run_full_set_case(
        label="Type 1 — TSP, no precheck",
        strict_order=True,
        problem_type="TSP",
        precheck=False,
    )

    _run_full_set_case(
        label="Type 1 — TSP, precheck",
        strict_order=True,
        problem_type="TSP",
        precheck=True,
    )

    _run_full_set_case(
        label="Type 2 — TSP, greedy",
        strict_order=False,
        problem_type="TSP",
        solver="greedy",
        precheck=False,
    )

    _run_full_set_case(
        label="Type 2 — HPP, greedy, precheck",
        strict_order=False,
        problem_type="HPP",
        solver="greedy",
        precheck=True,
    )

    # Full enumeration
    _run_full_set_case(
        label="All subsets — TSP, strict order",
        strict_order=True,
        problem_type="TSP",
        precheck=False,
        n=7,
        k_all=7,
        assert_full_enumeration=True,
    )


def test_full_set_evaluation_structured():
    _run_full_set_case_structured(
        label="Structured Type 1 — OUT:HPP",
        strict_order=True,
        problem_type="OUT:HPP",
    )

    _run_full_set_case_structured(
        label="Structured Type 2 — OUT:HPP, greedy",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
    )
    # Full enumeration
    _run_full_set_case_structured(
        label="All subsets — Structured Type 2 — OUT:HPP, greedy",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        k_all=20
    )


# =========================================================
# Manual execution
# =========================================================

if __name__ == "__main__":
    test_full_set_evaluation_non_structured()
    test_full_set_evaluation_structured()
