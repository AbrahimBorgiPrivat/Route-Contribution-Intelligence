import numbers
import numpy as np
from libraries.utils.algorithm.solvers.greedy import greedy_hpp_algorithm

def _assert_valid_hpp(path, L, D):
    n = len(D)
    assert isinstance(path, list)
    assert isinstance(L, numbers.Real)
    assert L >= 0
    assert set(path) == set(range(n))
    assert len(path) == n
    calc_L = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isclose(L, calc_L)

def test_case_A_free_hpp():
    print("\n=== CASE A: Free HPP ===")

    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)

    path, L = greedy_hpp_algorithm(D)

    print("Path:", path)
    print("Length:", L)

    _assert_valid_hpp(path, L, D)

def test_case_B_fixed_start():
    print("\n=== CASE B: Fixed start ===")

    D = np.array([
        [0, 1, 5],
        [2, 0, 1],
        [4, 3, 0],
    ], dtype=float)

    fixed = {"start": 0, "end": None}
    path, L = greedy_hpp_algorithm(D, fixed_endpoints=fixed)

    print("Path:", path)
    print("Length:", L)

    assert path[0] == 0
    _assert_valid_hpp(path, L, D)

def test_case_C_fixed_end():
    print("\n=== CASE C: Fixed end ===")

    D = np.array([
        [0, 1, 5],
        [2, 0, 1],
        [4, 3, 0],
    ], dtype=float)

    fixed = {"start": None, "end": 2}
    path, L = greedy_hpp_algorithm(D, fixed_endpoints=fixed)

    print("Path:", path)
    print("Length:", L)

    assert path[-1] == 2
    _assert_valid_hpp(path, L, D)

def test_case_D_fixed_start_and_end():
    print("\n=== CASE D: Fixed start and end ===")

    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ], dtype=float)

    fixed = {"start": 0, "end": 3}
    path, L = greedy_hpp_algorithm(D, fixed_endpoints=fixed)

    print("Path:", path)
    print("Length:", L)

    assert path[0] == 0
    assert path[-1] == 3
    _assert_valid_hpp(path, L, D)

def test_case_E_single_node():
    print("\n=== CASE E: Single node ===")

    D = np.array([[0.0]])

    path, L = greedy_hpp_algorithm(D)

    print("Path:", path)
    print("Length:", L)

    assert path == [0]
    assert np.isclose(L, 0.0)

def test_case_F_invalid_same_start_end():
    print("\n=== CASE F: Invalid same start/end ===")

    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)

    fixed = {"start": 0, "end": 0}

    try:
        _ = greedy_hpp_algorithm(D, fixed_endpoints=fixed)
        assert False, "Expected ValueError for same start and end"
    except ValueError as e:
        print("Correctly caught ValueError:", e)

def test_case_G_determinism():
    print("\n=== CASE G: Determinism ===")

    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)

    path1, L1 = greedy_hpp_algorithm(D)
    path2, L2 = greedy_hpp_algorithm(D)

    print("Run 1:", path1, L1)
    print("Run 2:", path2, L2)

    assert path1 == path2
    assert np.isclose(L1, L2)

if __name__ == "__main__":
    test_case_A_free_hpp()
    test_case_B_fixed_start()
    test_case_C_fixed_end()
    test_case_D_fixed_start_and_end()
    test_case_E_single_node()
    test_case_F_invalid_same_start_end()
    test_case_G_determinism()