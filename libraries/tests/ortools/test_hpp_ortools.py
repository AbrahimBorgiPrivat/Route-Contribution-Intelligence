import numpy as np
import pytest
from libraries.utils.algorithm.solvers.ortools import _hpp_ortools

def assert_valid_hpp(path, D):
    n = len(D)
    assert isinstance(path, list)
    assert len(path) == n
    assert sorted(path) == list(range(n))
    L = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isfinite(L)

def test_case_A_fast_path_fixed_start_end():
    print("\n=== CASE A: FAST PATH (fixed start & end) ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    fixed = {"start": 0, "end": 3}
    method = {"method": "GREEDY_DNN"}  # should be ignored
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert path[-1] == 3
    assert_valid_hpp(path, D)

def test_case_B_greedy_dnn():
    print("\n=== CASE B: GREEDY_DNN ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "GREEDY_DNN"}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_C_furthest_away():
    print("\n=== CASE C: FURTHEST_AWAY ===")
    D = np.array([
        [0, 1, 5, 9],
        [1, 0, 2, 4],
        [5, 2, 0, 3],
        [9, 4, 3, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "FURTHEST_AWAY", "n_edges": 2}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_D_extended_search():
    print("\n=== CASE D: EXTENDED_SEARCH ===")
    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "EXTENDED_SEARCH", "n_iterations": 2}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_E_extended_search_fixed_start():
    print("\n=== CASE E: EXTENDED_SEARCH (fixed start) ===")
    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ])
    fixed = {"start": 1, "end": None}
    method = {"method": "EXTENDED_SEARCH", "n_iterations": 2}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 1
    assert_valid_hpp(path, D)

def test_case_F_greedy():
    print("\n=== CASE F: GREEDY ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "GREEDY"}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_G_index_method():
    print("\n=== CASE G: INDEX ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "INDEX"}
    path, L = _hpp_ortools(
        D,
        fixed_endpoints=fixed,
        initial_point_method=method,
        ortools_time_limit=2,
    )
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert path[-1] == len(D) - 1
    assert_valid_hpp(path, D)

def test_case_H_unknown_method():
    print("\n=== CASE G: Unknown method ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ])
    fixed = {"start": None, "end": None}
    method = {"method": "NOT_A_METHOD"}
    with pytest.raises(ValueError, match="Unknown initial_point_method"):
        _ = _hpp_ortools(
            D,
            fixed_endpoints=fixed,
            initial_point_method=method,
            ortools_time_limit=1,
        )

if __name__ == "__main__":
    test_case_A_fast_path_fixed_start_end()
    test_case_B_greedy_dnn()
    test_case_C_furthest_away()
    test_case_D_extended_search()
    test_case_E_extended_search_fixed_start()
    test_case_F_greedy()
    test_case_G_index_method()
    test_case_H_unknown_method()