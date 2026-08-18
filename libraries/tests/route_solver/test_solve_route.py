import numbers
import numpy as np
from typing import List
from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.algorithm.single_route.route_solver import solve_route

def _run_solve_route_case(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n: int = 10,
    solver: str = "ortools",
    L_u: float | List[float] | None = None,
    ):
    print("\n====================================================")
    print(f"TEST SOLVE_ROUTE: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    D, _ = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.1,
        outlier_fraction=0.1,
    )
    R = list(range(n))
    L_u_used = L_u if L_u is not None else 0.0
    R_seq, L = solve_route(
        D=D,
        R=R,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        L_u=L_u_used,
        deterministic=True,
        ortools_time_limit=3,
    )
    print(f"Route sequence: {R_seq}")
    print(f"Route length:   {L:.4f}")
    assert isinstance(R_seq, list)
    assert isinstance(L, numbers.Real)
    assert len(R_seq) == len(R)
    assert set(R_seq) == set(R)
    assert all(isinstance(x, int) for x in R_seq)
    assert all(0 <= x < n for x in R_seq)
    assert L >= 0
    if strict_order:
        assert R_seq == R, "Strict order must preserve input order"
    print("✔ Test passed")

def test_solve_route():
    _run_solve_route_case(
        label="Type 1 — strict order, TSP",
        strict_order=True,
        problem_type="TSP",
    )

    _run_solve_route_case(
        label="Type 1 — strict order, HPP",
        strict_order=True,
        problem_type="HPP",
    )

    _run_solve_route_case(
        label="Type 2 — TSP, ortools",
        strict_order=False,
        problem_type="TSP",
        solver="ortools",
    )

    _run_solve_route_case(
        label="Type 2 — TSP, greedy",
        strict_order=False,
        problem_type="TSP",
        solver="greedy",
    )

    _run_solve_route_case(
        label="Type 2 — TSP, exact (reference)",
        strict_order=False,
        problem_type="TSP",
        solver="exact",
    )

    _run_solve_route_case(
        label="Type 2 — HPP, ortools",
        strict_order=False,
        problem_type="HPP",
        solver="ortools",
    )

    _run_solve_route_case(
        label="Type 2 — HPP, greedy",
        strict_order=False,
        problem_type="HPP",
        solver="greedy",
    )

    _run_solve_route_case(
        label="Type 2 — HPP, exact (reference)",
        strict_order=False,
        problem_type="HPP",
        solver="exact",
    )
    
    rng = np.random.default_rng(42)
    L_u_vec = rng.uniform(0.5, 3.0, size=10)
    _run_solve_route_case(
        label="Type 2 — HPP, vector L_u",
        strict_order=False,
        problem_type="HPP",
        solver="greedy",
        L_u=L_u_vec,
    )


def test_type2_route_adds_scalar_L_u_to_length():
    D = np.array([
        [0.0, 2.0, 5.0],
        [2.0, 0.0, 1.0],
        [5.0, 1.0, 0.0],
    ])
    R = [0, 1, 2]

    _, L_without = solve_route(
        D=D,
        R=R,
        strict_order=False,
        problem_type="HPP",
        solver="exact",
        L_u=0.0,
        deterministic=True,
        ortools_time_limit=3,
    )
    _, L_with = solve_route(
        D=D,
        R=R,
        strict_order=False,
        problem_type="HPP",
        solver="exact",
        L_u=30.0,
        deterministic=True,
        ortools_time_limit=3,
    )

    assert np.isclose(L_with - L_without, 90.0)


if __name__ == "__main__":
    test_solve_route()
