import numpy as np

from libraries.utils.algorithm.solvers.greedy import greedy_hpp_cheapest_insertion


def assert_valid_hpp(path, D):
    n = len(D)
    assert isinstance(path, list)
    assert len(path) == n
    assert sorted(path) == list(range(n))
    L = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isfinite(L)
    assert L >= 0

def test_case_A_small_symmetric_free():
    print("\n=== CASE A: Small symmetric HPP (free) ===")
    D = np.array([
        [0, 1, 9],
        [1, 0, 8],
        [9, 8, 0],
    ], dtype=float)
    path, L = greedy_hpp_cheapest_insertion(D)
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_B_asymmetric_free():
    print("\n=== CASE B: Asymmetric HPP (free) ===")
    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    path, L = greedy_hpp_cheapest_insertion(D)
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_C_fixed_start():
    print("\n=== CASE C: Fixed start ===")
    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    fixed = {"start": 0, "end": None}
    path, L = greedy_hpp_cheapest_insertion(D, fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert_valid_hpp(path, D)

def test_case_D_fixed_end():
    print("\n=== CASE D: Fixed end ===")
    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    fixed = {"start": None, "end": 3}
    path, L = greedy_hpp_cheapest_insertion(D, fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[-1] == 3
    assert_valid_hpp(path, D)

def test_case_E_fixed_start_and_end():
    print("\n=== CASE E: Fixed start and end ===")
    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ], dtype=float)
    fixed = {"start": 0, "end": 3}
    path, L = greedy_hpp_cheapest_insertion(D, fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert path[-1] == 3
    assert_valid_hpp(path, D)

def test_case_F_single_node():
    print("\n=== CASE F: Single node ===")

    D = np.array([[0.0]])
    path, L = greedy_hpp_cheapest_insertion(D)

    print("Path:", path)
    print("Length:", L)

    assert path == [0]
    assert np.isclose(L, 0.0)

def test_case_G_deterministic():
    print("\n=== CASE G: Determinism ===")
    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    path1, L1 = greedy_hpp_cheapest_insertion(D)
    path2, L2 = greedy_hpp_cheapest_insertion(D)
    print("Path 1:", path1, "Length:", L1)
    print("Path 2:", path2, "Length:", L2)
    assert path1 == path2
    assert np.isclose(L1, L2)

def test_case_H_non_square_distance_matrix_raises() -> None:
    """
    Covers line 225:
    Non-square distance matrix must raise ValueError.
    """
    print("\n=== CASE H: Non-square distance matrix ===")

    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
    ], dtype=float) 
    try:
        greedy_hpp_cheapest_insertion(D)
        assert False, "Expected ValueError for non-square matrix"
    except ValueError as e:
        assert "square matrix" in str(e)

def test_case_I_fixed_start_out_of_bounds() -> None:
    """
    Covers line 232:
    fixed start < 0 or >= n must raise ValueError.
    """
    print("\n=== CASE I: Fixed start out of bounds ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)
    try:
        greedy_hpp_cheapest_insertion(D, {"start": 5, "end": None})
        assert False, "Expected ValueError for fixed start out of bounds"
    except ValueError as e:
        assert "fixed start" in str(e)

def test_case_J_fixed_end_out_of_bounds() -> None:
    """
    Covers line 234:
    fixed end < 0 or >= n must raise ValueError.
    """
    print("\n=== CASE J: Fixed end out of bounds ===")

    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)

    try:
        greedy_hpp_cheapest_insertion(D, {"start": None, "end": -1})
        assert False, "Expected ValueError for fixed end out of bounds"
    except ValueError as e:
        assert "fixed end" in str(e)

def test_case_K_fixed_start_equals_end_raises() -> None:
    """
    Covers line 236:
    start == end with n > 1 must raise ValueError.
    """
    print("\n=== CASE K: Fixed start equals fixed end ===")
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ], dtype=float)
    try:
        greedy_hpp_cheapest_insertion(D, {"start": 1, "end": 1})
        assert False, "Expected ValueError when start == end and n > 1"
    except ValueError as e:
        assert "Fixed start and end cannot be the same" in str(e)

def test_case_L_single_node_path_length_zero() -> None:
    """
    Covers line 240:
    Path length must be 0.0 for single-node input.
    """
    print("\n=== CASE L: Single-node path length ===")
    D = np.array([[0.0]])
    path, L = greedy_hpp_cheapest_insertion(D)
    assert path == [0]
    assert np.isclose(L, 0.0)

def test_case_M_best_seed_candidates_fallback() -> None:
    """
    Covers lines 245 and 249:
    - n > 1
    - initial candidates empty
    - fallback candidate list used
    """
    print("\n=== CASE M: best_seed candidate fallback ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)
    path, _ = greedy_hpp_cheapest_insertion(D, {"start": 0, "end": 1})
    assert path[0] == 0
    assert path[-1] == 1
    assert_valid_hpp(path, D)

def test_case_N_best_seed_fixed_end_single_node() -> None:
    """
    Covers line 255:
    _best_seed_for_fixed_end returns [e] when n == 1.
    """
    print("\n=== CASE N: best_seed_for_fixed_end n==1 ===")
    D = np.array([[0.0]])
    path, L = greedy_hpp_cheapest_insertion(D, {"start": None, "end": 0})
    assert path == [0]
    assert np.isclose(L, 0.0)

def test_case_O_best_seed_fixed_end_candidate_fallback() -> None:
    """
    Covers line 258:
    Fallback candidate selection when initial candidates empty.
    """
    print("\n=== CASE O: best_seed_for_fixed_end candidate fallback ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)
    path, L = greedy_hpp_cheapest_insertion(D, {"start": 0, "end": 1})
    assert path[0] == 0
    assert path[-1] == 1
    assert_valid_hpp(path, D)

def test_case_P_empty_distance_matrix() -> None:
    """
    Covers line 317:
    n == 0 returns empty path and zero length.
    """
    print("\n=== CASE P: Empty distance matrix ===")
    D = np.empty((0, 0))
    path, L = greedy_hpp_cheapest_insertion(D)
    assert path == []
    assert np.isclose(L, 0.0)

if __name__ == "__main__":
    test_case_A_small_symmetric_free()
    test_case_B_asymmetric_free()
    test_case_C_fixed_start()
    test_case_D_fixed_end()
    test_case_E_fixed_start_and_end()
    test_case_F_single_node()
    test_case_G_deterministic()
    test_case_H_non_square_distance_matrix_raises()
    test_case_I_fixed_start_out_of_bounds()
    test_case_J_fixed_end_out_of_bounds()
    test_case_K_fixed_start_equals_end_raises()
    test_case_L_single_node_path_length_zero()
    test_case_M_best_seed_candidates_fallback()
    test_case_N_best_seed_fixed_end_single_node()
    test_case_O_best_seed_fixed_end_candidate_fallback()
    test_case_P_empty_distance_matrix()
