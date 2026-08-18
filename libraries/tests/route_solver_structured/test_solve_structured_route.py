import numbers

from libraries.utils.experiments.simulations_structured_route import (
    simulate_structured_route,
)
from libraries.utils.algorithm.single_route.structured_route_builder import (
    build_structured_route_data,
)
from libraries.utils.algorithm.single_route.route_solver_structured import (
    solve_structured_route,
    apply_s_to_structured_model
)


def _run_solve_structured_route_case(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n_units: int = 5,
    min_unit_size: int = 2,
    max_unit_size: int = 4,
    solver: str = "ortools",
):
    print("\n====================================================")
    print(f"TEST SOLVE_STRUCTURED_ROUTE: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    # --------------------------------------------------
    # 1) Generate flat structured instance
    # --------------------------------------------------
    D_big, nodes, _ = simulate_structured_route(
        n_units=n_units,
        min_unit_size=min_unit_size,
        max_unit_size=max_unit_size,
        seed=123,
        asymmetry_strength=0.1,
        cluster_strength=0.6,
        outlier_fraction=0.0,
    )

    # --------------------------------------------------
    # 2) Build structured route data
    # --------------------------------------------------
    D_outer, inner_models, D_full = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    all_addresses = []
    for m in inner_models:
        all_addresses.extend(m["route_nodes"])
    all_addresses = set(all_addresses)
    R = list(range(len(all_addresses)))

    # --------------------------------------------------
    # 3) Solve structured route
    # --------------------------------------------------
    R_seq, L, inner_cache, outer_cache = solve_structured_route(
        D_outer=D_outer,
        D_all=D_full,
        R=R,
        inner_models=inner_models if not strict_order else [],
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        deterministic=True,
        ortools_time_limit=3,
    )

    # --------------------------------------------------
    # 4) Output
    # --------------------------------------------------
    print(f"Route sequence: {R_seq}")
    print(f"Route length:   {L:.4f}")
    print(f"Inner cache size: {len(inner_cache)}")
    print(f"Outer cache size: {len(outer_cache)}")

    # --------------------------------------------------
    # 5) Assertions
    # --------------------------------------------------
    assert isinstance(R_seq, list)
    assert isinstance(L, numbers.Real)
    assert L >= 0
    assert set(R_seq) == all_addresses
    assert len(R_seq) == len(all_addresses)
    assert all(isinstance(x, int) for x in R_seq)
    if strict_order:
        assert inner_cache == {}
        assert outer_cache == {}
        assert R_seq == R
    else:
        assert isinstance(inner_cache, dict)
        assert isinstance(outer_cache, dict)
        assert len(inner_cache) > 0
        assert len(outer_cache) > 0

def _run_solve_structured_route_after_removal(strict_order: bool):
    """
    Integration test:
    simulate -> build -> apply_S_to_structured_model -> solve_structured_route
    """

    print("\n====================================================")
    print("TEST SOLVE_STRUCTURED_ROUTE AFTER REMOVAL")
    print(f"  strict_order={strict_order}")
    print("\n====================================================")
    

    # --------------------------------------------------
    # 1) Simulate structured instance
    # --------------------------------------------------
    D_big, nodes, _ = simulate_structured_route(
        n_units=4,
        min_unit_size=3,
        max_unit_size=4,
        seed=2024,
        asymmetry_strength=0.1,
    )

    # --------------------------------------------------
    # 2) Build structured model
    # --------------------------------------------------
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes"])
    all_addresses = set(R)

    # --------------------------------------------------
    # 3) Remove a subset of addresses (partial removal)
    # --------------------------------------------------
    S = {0, 1, 2, 7}

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
        R=R,
        inner_models=inner_models,
        S=S,
    )
    remaining_addresses = all_addresses - S

    # --------------------------------------------------
    # 4) Solve structured route after removal (Type 2)
    # --------------------------------------------------
    R_seq, L, inner_cache, outer_cache = solve_structured_route(
        D_outer=D_outer_new,
        D_all=D_all_new,
        R=R_local_reduced,
        inner_models=inner_models_new,
        strict_order=strict_order,
        problem_type="OUT:HPP",
        solver="greedy",
        deterministic=True,
    )
    inv_address_index_map = {
        new: old for old, new in address_index_map.items()
    }
    R_seq_orig = [inv_address_index_map[i] for i in R_seq]
    
    # --------------------------------------------------
    # 5) Assertions
    # --------------------------------------------------
    print(f"Route sequence after removal: {R_seq}")
    print(f"Route length after removal:   {L:.4f}")
    print(f"Route sequence after removal (global): {R_seq_orig}")
    assert isinstance(R_seq, list)
    assert isinstance(L, float)
    assert L >= 0
    assert set(R_seq) == set(range(len(R_local_reduced)))
    assert len(R_seq) == len(R_local_reduced)
    assert set(R_seq_orig) == remaining_addresses
    assert len(R_seq_orig) == len(remaining_addresses)
    if strict_order==False:
        assert isinstance(inner_cache, dict)
        assert isinstance(outer_cache, dict)
        assert len(inner_cache) > 0
        assert len(outer_cache) > 0
        for (unit_global, route_nodes_global), (cached_route_global, _) in inner_cache.items():
            assert not (set(route_nodes_global) & S), (
                f"inner_cache key contains removed addresses: {route_nodes_global} ∩ {S}"
            )
            assert not (set(cached_route_global) & S), (
                f"inner_cache route contains removed addresses: {cached_route_global} ∩ {S}"
            )
        for outer_units_global, (outer_order_global, _) in outer_cache.items():
            for u in outer_order_global:
                assert isinstance(u, int)

def test_solve_structured_route():
    _run_solve_structured_route_case(
        label="Structured Type 1 — OUT:TSP",
        strict_order=True,
        problem_type="OUT:TSP",
    )

    _run_solve_structured_route_case(
        label="Structured Type 1 — OUT:HPP",
        strict_order=True,
        problem_type="OUT:HPP",
    )

    _run_solve_structured_route_case(
        label="Structured Type 2 — OUT:TSP, ortools",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="ortools",
    )

    _run_solve_structured_route_case(
        label="Structured Type 2 — OUT:TSP, greedy",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="greedy",
    )

    _run_solve_structured_route_case(
        label="Structured Type 2 — OUT:HPP, ortools",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="ortools",
    )

    _run_solve_structured_route_case(
        label="Structured Type 2 — OUT:HPP, greedy",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
    )
    _run_solve_structured_route_after_removal(
        strict_order=False
    )
    _run_solve_structured_route_after_removal(
        strict_order=True
    )


if __name__ == "__main__":
    test_solve_structured_route()
