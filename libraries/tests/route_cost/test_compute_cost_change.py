import numbers
import numpy as np
from typing import List, Set

from libraries.utils.algorithm.single_route.route_costs import compute_cost_change
from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import (
    simulate_structured_route,
)
from libraries.utils.algorithm.single_route.structured_route_builder import (
    build_structured_route_data,
)


# =========================================================
# Helper 1: Non-structured cases (TSP / HPP)
# =========================================================

def _run_compute_cost_change_case_non_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n: int = 10,
    solver: str = "ortools",
    L_u: float | List[float] | None = None,
):
    print("\n====================================================")
    print(f"TEST COMPUTE_COST_CHANGE (NON-STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    # Simulate distance matrix
    D, _ = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.1,
        outlier_fraction=0.1,
    )

    R = list(range(n))
    S: Set[int] = {1, n - 2}
    L_u_used = L_u if L_u is not None else 0.0

    delta, R_new = compute_cost_change(
        D=D,
        R=R,
        S=S,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        L_u=L_u_used,
        include_path=True,
        deterministic=True,
        ortools_time_limit=3,
    )

    print("Delta length:", delta)
    print("New route:", R_new)

    assert isinstance(delta, numbers.Real)
    assert isinstance(R_new, list)
    assert set(R_new) == set(R) - S
    assert len(R_new) == len(R) - len(S)

    if strict_order:
        # order must be preserved
        assert R_new == [i for i in R if i not in S]

    print("✔ Test passed")


# =========================================================
# Helper 2: Structured cases (OUT:TSP / OUT:HPP)
# =========================================================

def _run_compute_cost_change_case_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n_units: int = 4,
    solver: str = "ortools",
):
    print("\n====================================================")
    print(f"TEST COMPUTE_COST_CHANGE (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    # Simulate structured instance
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
    all_addresses = set(R)

    # Remove a few addresses (partial removal)
    S: Set[int] = set(list(R)[:3])

    delta, R_new, inner_cache, outer_cache = compute_cost_change(
        D=D_outer,
        R=R,
        S=S,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        include_path=True,
        D_all=D_all,
        inner_models=inner_models,
        deterministic=True,
    )

    print("Delta length:", delta)
    print("New route:", R_new)

    assert isinstance(delta, numbers.Real)
    assert isinstance(R_new, list)
    assert set(R_new) == all_addresses - S
    assert len(R_new) == len(all_addresses) - len(S)

    if strict_order:
        assert inner_cache == {}
        assert outer_cache == {}
    else:
        assert isinstance(inner_cache, dict)
        assert isinstance(outer_cache, dict)
        assert len(inner_cache) > 0
        assert len(outer_cache) > 0
        
# =========================================================
# Test runners
# =========================================================

def test_compute_cost_change_non_structured():
    _run_compute_cost_change_case_non_structured(
        label="Type 1 — strict order, TSP",
        strict_order=True,
        problem_type="TSP",
    )

    _run_compute_cost_change_case_non_structured(
        label="Type 1 — strict order, HPP",
        strict_order=True,
        problem_type="HPP",
    )

    _run_compute_cost_change_case_non_structured(
        label="Type 2 — TSP, greedy",
        strict_order=False,
        problem_type="TSP",
        solver="greedy",
    )

    _run_compute_cost_change_case_non_structured(
        label="Type 2 — HPP, greedy",
        strict_order=False,
        problem_type="HPP",
        solver="greedy",
    )

    rng = np.random.default_rng(42)
    L_u_vec = rng.uniform(0.5, 3.0, size=10)

    _run_compute_cost_change_case_non_structured(
        label="Type 2 — HPP with vector L_u",
        strict_order=False,
        problem_type="HPP",
        solver="greedy",
        L_u=L_u_vec,
    )


def test_compute_cost_change_structured():
    _run_compute_cost_change_case_structured(
        label="Structured Type 1 — OUT:HPP",
        strict_order=True,
        problem_type="OUT:HPP",
    )

    _run_compute_cost_change_case_structured(
        label="Structured Type 2 — OUT:HPP, greedy",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
    )


# =========================================================
# Manual execution
# =========================================================

if __name__ == "__main__":
    test_compute_cost_change_non_structured()
    test_compute_cost_change_structured()
