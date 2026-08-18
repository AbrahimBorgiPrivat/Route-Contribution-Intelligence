import numpy as np

from libraries.utils.experiments.simulations_structured_route import (
    simulate_structured_route,
)
from libraries.utils.algorithm.single_route.structured_route_builder import (
    build_structured_route_data,
)

def print_matrix(D, name="Matrix"):
    print(f"\n{name}:")
    with np.printoptions(precision=3, suppress=True):
        print(D)

def test_case_1_basic_shapes_and_types():
    """
    Basic test: verify shapes and return types.
    """
    print("\n=== TEST CASE 1: Basic structured builder ===")
    D_big, nodes, p = simulate_structured_route(
        n_units=3,
        min_unit_size=2,
        max_unit_size=2,
        seed=42,
        asymmetry_strength=0.0,
    )
    D_outer, inner_models, D_full = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    print_matrix(D_big, "D_big")
    print_matrix(D_outer, "D_outer")
    print_matrix(D_full, "D_full")
    n_units = 3
    n_addresses = len(p)
    assert D_outer.shape == (n_units, n_units)
    assert D_full.shape == (n_addresses, n_addresses)
    assert len(inner_models) == n_units
    assert np.allclose(np.diag(D_outer), 0.0)
    assert np.allclose(np.diag(D_full), 0.0)

def test_case_2_route_number_and_unit_semantics():
    """
    D_full semantics:
    """
    print("\n=== TEST CASE 2: route_number + unit semantics ===")
    D_big, nodes, _ = simulate_structured_route(
        n_units=4,
        min_unit_size=1,
        max_unit_size=3,
        seed=123,
    )
    _, _, D_full = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    addr_nodes = {n["route_number"]: n for n in nodes if n["type"] == "address"}
    unit_starts = {n["unit"]: n["m_index"] for n in nodes if n["type"] == "start"}
    unit_ends = {n["unit"]: n["m_index"] for n in nodes if n["type"] == "end"}
    for i in range(D_full.shape[0]):
        for j in range(D_full.shape[1]):
            ni = addr_nodes[i]
            nj = addr_nodes[j]
            mi = ni["m_index"]
            mj = nj["m_index"]
            if ni["unit"] == nj["unit"]:
                expected = D_big[mi, mj]
            else:
                expected = (
                    D_big[mi, unit_ends[ni["unit"]]]
                    + D_big[unit_ends[ni["unit"]], unit_starts[nj["unit"]]]
                    + D_big[unit_starts[nj["unit"]], mj]
                )
            assert np.isclose(D_full[i, j], expected)

def test_case_3_outer_distance_definition():
    """
    Verify that D_outer[i,j] == distance from end of unit i to start of unit j.
    """
    print("\n=== TEST CASE 3: D_outer semantics ===")
    D_big, nodes, _ = simulate_structured_route(
        n_units=5,
        min_unit_size=2,
        max_unit_size=3,
        seed=321,
    )
    D_outer, _, _ = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    starts = {}
    ends = {}
    for n in nodes:
        if n["type"] == "start":
            starts[n["unit"]] = n["m_index"]
        elif n["type"] == "end":
            ends[n["unit"]] = n["m_index"]
    unit_ids = sorted(starts.keys())
    for i, ui in enumerate(unit_ids):
        for j, uj in enumerate(unit_ids):
            if i == j:
                assert np.isclose(D_outer[i, j], 0.0)
            else:
                expected = D_big[ends[ui], starts[uj]]
                assert np.isclose(D_outer[i, j], expected)

def test_case_4_inner_models_structure():
    """
    Verify inner_models content and D_inner correctness.
    """
    print("\n=== TEST CASE 4: inner_models correctness ===")
    D_big, nodes, _ = simulate_structured_route(
        n_units=4,
        min_unit_size=2,
        max_unit_size=4,
        seed=77,
    )
    _, inner_models, _ = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    for model in inner_models:
        route_nodes = model["route_nodes"]
        D_inner = model["D_inner"]
        assert model["entry_index"] == 0
        assert model["exit_index"] == D_inner.shape[0] - 1
        k = len(route_nodes)
        assert D_inner.shape == (k + 2, k + 2)
        assert len(route_nodes) == len(set(route_nodes))

def test_case_5_known_matrix_builder():
    """
    Deterministic test with a hand-crafted 10x10 matrix verifying structured Type 1 semantics.
    """
    print("\n=== TEST CASE 5: Deterministic structured builder ===")
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
    D_outer, _, D_full = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    expected_D_outer = np.array([
        [0.0, 1.0],
        [9.0, 0.0],
    ])
    assert np.allclose(D_outer, expected_D_outer)

def test_case_6_known_asymmetric_6x6():
    """
    Deterministic asymmetric example:
    """
    print("\n=== TEST CASE 6: Known asymmetric 6x6 example ===")
    nodes = [
        {"m_index": 0, "unit": 0, "type": "start",   "route_number": None},
        {"m_index": 1, "unit": 0, "type": "address", "route_number": 0},
        {"m_index": 2, "unit": 0, "type": "end",     "route_number": None},
        {"m_index": 3, "unit": 1, "type": "start",   "route_number": None},
        {"m_index": 4, "unit": 1, "type": "address", "route_number": 1},
        {"m_index": 5, "unit": 1, "type": "end",     "route_number": None},
    ]
    D_big = np.array([
        [0, 1, 2, 10, 11, 12],
        [2, 0, 1, 20, 21, 22],
        [3, 4, 0, 10, 31, 32],
        [13, 14, 15, 0, 1, 2],
        [23, 24, 25, 2, 0, 1],
        [33, 34, 35, 3, 4, 0],
    ], dtype=float)

    D_outer, _, D_full = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    print_matrix(D_big, "D_big")
    print_matrix(D_outer, "D_outer")
    print_matrix(D_full, "D_full")
    assert D_outer[0, 1] == 10
    assert D_outer[1, 0] == 33
    assert not np.isclose(D_outer[0, 1], D_outer[1, 0])

if __name__ == "__main__":
    test_case_1_basic_shapes_and_types()
    test_case_2_route_number_and_unit_semantics()
    test_case_3_outer_distance_definition()
    test_case_4_inner_models_structure()
    test_case_5_known_matrix_builder()
    test_case_6_known_asymmetric_6x6()