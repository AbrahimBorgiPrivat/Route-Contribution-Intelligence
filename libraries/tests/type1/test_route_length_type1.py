import numpy as np
from libraries.utils.algorithm.solvers.type1 import route_length_type1

def test_case_A_full_route_TSP_default():
    print("\n=== CASE A1: Full route (TSP, default) ===")
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0]
    ])
    R = [0, 1, 2]
    L = route_length_type1(D, R)
    expected = 1 + 3 + 2  # 0→1, 1→2, 2→0
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_A_full_route_HPP():
    print("\n=== CASE A2: Full route (HPP) ===")
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0]
    ])
    R = [0, 1, 2]
    L = route_length_type1(D, R, problem_type="HPP")
    expected = 1 + 3 
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_B_partial_route_TSP():
    print("\n=== CASE B1: Partial route (TSP) ===")
    D = np.array([
        [0, 1, 2, 4],
        [1, 0, 5, 7],
        [2, 5, 0, 1],
        [4, 7, 1, 0]
    ])
    R = [1, 3, 2]
    expected = 7 + 1 + 5  # 1→3, 3→2, 2→1
    L = route_length_type1(D, R, problem_type="TSP")
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_B_partial_route_HPP():
    print("\n=== CASE B2: Partial route (HPP) ===")
    D = np.array([
        [0, 1, 2, 4],
        [1, 0, 5, 7],
        [2, 5, 0, 1],
        [4, 7, 1, 0]
    ])
    R = [1, 3, 2]
    expected = 7 + 1  # 1→3, 3→2
    L = route_length_type1(D, R, problem_type="HPP")
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_C_Lu_scalar():
    print("\n=== CASE C: Scalar L_u ===")
    D = np.array([
        [0, 2, 2],
        [2, 0, 2],
        [2, 2, 0]
    ])
    R = [0, 1, 2]
    L_u = 0.5
    L = route_length_type1(D, R, L_u=L_u, problem_type="TSP")
    expected = (2 + 2 + 2) + 3 * 0.5
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_D_Lu_vector_HPP():
    print("\n=== CASE D: Vector L_u (HPP) ===")
    D = np.array([
        [0, 2, 2],
        [2, 0, 2],
        [2, 2, 0]
    ])
    R = [0, 1, 2]
    L_u = [0.2, 0.3, 0.4]
    L = route_length_type1(D, R, L_u=L_u, problem_type="HPP")
    expected = (2 + 2) + sum(L_u) 
    print("Expected:", expected)
    print("Got:     ", L)
    assert np.isclose(L, expected)

def test_case_E_invalid_route():
    print("\n=== CASE E: Invalid route ===")
    D = np.array([
        [0, 1],
        [1, 0]
    ])
    R_invalid = [0, 1, 2]
    try:
        _ = route_length_type1(D, R_invalid)
        print("ERROR: Expected failure but function succeeded.")
        assert False
    except ValueError as e:
        print("Correctly caught ValueError:", e)

if __name__ == "__main__":
    test_case_A_full_route_TSP_default()
    test_case_A_full_route_HPP()
    test_case_B_partial_route_TSP()
    test_case_B_partial_route_HPP()
    test_case_C_Lu_scalar()
    test_case_D_Lu_vector_HPP()
    test_case_E_invalid_route()