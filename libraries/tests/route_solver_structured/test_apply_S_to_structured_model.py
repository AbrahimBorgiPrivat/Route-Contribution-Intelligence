import numpy as np

from libraries.utils.experiments.simulations_structured_route import (
    simulate_structured_route,
)
from libraries.utils.algorithm.single_route.structured_route_builder import (
    build_structured_route_data,
)
from libraries.utils.algorithm.single_route.route_solver_structured import (
    apply_s_to_structured_model,
)

def test_case_1_deterministic_reduction():
    """
    Deterministic test:
    """
    print("\n=== TEST CASE 1: Deterministic reduction ===")
    nodes = [
        {"m_index": 0, "unit": 0, "type": "start",   "route_number": None},
        {"m_index": 1, "unit": 0, "type": "address", "route_number": 0},
        {"m_index": 2, "unit": 0, "type": "address", "route_number": 1},
        {"m_index": 3, "unit": 0, "type": "address", "route_number": 2},
        {"m_index": 4, "unit": 0, "type": "end",     "route_number": None},
        {"m_index": 5, "unit": 1, "type": "start",   "route_number": None},
        {"m_index": 6, "unit": 1, "type": "address", "route_number": 3},
        {"m_index": 7, "unit": 1, "type": "address", "route_number": 4},
        {"m_index": 8, "unit": 1, "type": "address", "route_number": 5},
        {"m_index": 9, "unit": 1, "type": "end",     "route_number": None},
    ]
    n = 10
    D_big = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D_big[i, j] = abs(i - j)
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = list(range(6))
    S = {4} 
    (
        D_outer_new,
        D_all_new,
        R_local,
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
    assert R_local == list(range(5))
    assert set(address_index_map.keys()) == {0, 1, 2, 3, 5}
    assert set(address_index_map.values()) == set(range(5))
    assert D_all_new.shape == (5, 5)
    assert len(inner_models_new) == 2
    assert D_outer_new.shape == (2, 2)
    globals_after = set()
    for m in inner_models_new:
        globals_after |= set(m["route_nodes_global"])
    assert globals_after == {0, 1, 2, 3, 5}

def test_case_2_simulated_partial_removal():
    """
    Simulated test:
    - remove some addresses
    - no unit is fully removed
    """
    print("\n=== TEST CASE 2: Simulated partial removal ===")
    D_big, nodes, _ = simulate_structured_route(
        n_units=4,
        min_unit_size=3,
        max_unit_size=4,
        seed=123,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    S = {
        inner_models[0]["route_nodes_global"][0],
        inner_models[1]["route_nodes_global"][0],
    }
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    (
        D_outer_new,
        D_all_new,
        R_local,
        inner_models_new,
        _,
        _,
    ) = apply_s_to_structured_model(
        D_outer=D_outer,
        D_all=D_all,
        R=R,
        inner_models=inner_models,
        S=S,
    )
    assert len(R_local) == len(R) - len(S)
    assert D_all_new.shape == (len(R_local), len(R_local))
    assert len(inner_models_new) == len(inner_models)
    assert D_outer_new.shape == D_outer.shape

def test_case_3_simulated_full_unit_removal():
    """
    Simulated test:
    - remove all addresses from one unit
    - outer graph must be reduced
    """
    print("\n=== TEST CASE 3: Simulated full unit removal ===")
    D_big, nodes, _ = simulate_structured_route(
        n_units=5,
        min_unit_size=2,
        max_unit_size=3,
        seed=999,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    S = set(inner_models[0]["route_nodes_global"])
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    (
        D_outer_new,
        D_all_new,
        R_local,
        inner_models_new,
        outer_index_map,
        _,
    ) = apply_s_to_structured_model(
        D_outer=D_outer,
        D_all=D_all,
        R=R,
        inner_models=inner_models,
        S=S,
    )
    assert len(inner_models_new) == len(inner_models) - 1
    assert D_outer_new.shape == (
        len(inner_models) - 1,
        len(inner_models) - 1,
    )
    assert len(R_local) == len(R) - len(S)
    assert D_all_new.shape == (len(R_local), len(R_local))
    assert set(outer_index_map.values()) == set(range(len(inner_models_new)))

def test_case_4_easy_global_local_example():
    """
    Very small example where global/local mapping is obvious.
    """
    print("\n=== TEST CASE 4: Easy global/local example ===")
    nodes = [
        {"m_index": 0, "unit": 2, "type": "start",   "route_number": None},
        {"m_index": 1, "unit": 2, "type": "address", "route_number": 0},
        {"m_index": 2, "unit": 2, "type": "address", "route_number": 1},
        {"m_index": 3, "unit": 2, "type": "end",     "route_number": None},
        {"m_index": 4, "unit": 1, "type": "start",   "route_number": None},
        {"m_index": 5, "unit": 1, "type": "address", "route_number": 2},
        {"m_index": 6, "unit": 1, "type": "end",     "route_number": None},
    ]
    n = 7
    D_big = np.arange(n * n, dtype=float).reshape(n, n)
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = [0, 1, 2]
    S = {0}
    (
        D_outer_new,
        _,
        R_local,
        inner_models_new,
        outer_index_map,
        address_index_map,
    ) = apply_s_to_structured_model(
        D_outer=D_outer,
        D_all=D_all,
        R=R,
        inner_models=inner_models,
        S=S,
    )
    assert address_index_map == {1: 0, 2: 1}
    assert R_local == [0, 1]
    unit0 = next(m for m in inner_models_new if m["outer_index_global"] == 2)
    assert unit0["route_nodes_global"] == [1]
    assert unit0["route_nodes"] == [0]
    unit1 = next(m for m in inner_models_new if m["outer_index_global"] == 1)
    assert unit1["route_nodes_global"] == [2]
    assert unit1["route_nodes"] == [1]


if __name__ == "__main__":
    test_case_1_deterministic_reduction()
    test_case_2_simulated_partial_removal()
    test_case_3_simulated_full_unit_removal()
    test_case_4_easy_global_local_example()
