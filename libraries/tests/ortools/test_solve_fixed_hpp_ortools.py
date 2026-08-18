import numpy as np
from libraries.utils.algorithm.solvers.ortools import _solve_fixed_hpp_ortools

def test_case_A_basic_fixed_start_end():
    """
    Basic sanity check:
    - fixed start and end
    - path must start/end correctly
    - path must be a Hamiltonian path
    """
    print("\n=== CASE A: Basic fixed start/end ===")

    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])

    start, end = 0, 2
    path, L = _solve_fixed_hpp_ortools(D, start, end, ortools_time_limit=2)

    print("Path:", path)
    print("Length:", L)
    assert path[0] == start
    assert path[-1] == end

    # Must visit all nodes exactly once
    assert sorted(path) == list(range(len(D)))

    # Length must match edge sum
    expected = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isclose(L, expected)


def test_case_B_different_fixed_endpoints():
    """
    Another fixed-endpoint configuration.
    """
    print("\n=== CASE B: Different fixed endpoints ===")

    D = np.array([
        [0, 1, 4],
        [2, 0, 3],
        [5, 6, 0],
    ])

    start, end = 2, 1
    path, L = _solve_fixed_hpp_ortools(D, start, end, ortools_time_limit=2)

    print("Path:", path)
    print("Length:", L)

    assert path[0] == start
    assert path[-1] == end
    assert sorted(path) == [0, 1, 2]


def test_case_C_single_possible_path():
    """
    n=2 is the trivial HPP case.
    """
    print("\n=== CASE C: Two-node path ===")

    D = np.array([
        [0, 7],
        [3, 0],
    ])

    start, end = 0, 1
    path, L = _solve_fixed_hpp_ortools(D, start, end, ortools_time_limit=1)

    print("Path:", path)
    print("Length:", L)

    assert path == [0, 1]
    assert np.isclose(L, D[0, 1])

def test_case_D_start_equals_end():
    """
    start == end is allowed: OR-Tools returns a cycle.
    The solver should return a valid route, not raise.
    """
    print("\n=== CASE D: start == end ===")
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ])
    start = end = 1
    path, L = _solve_fixed_hpp_ortools(D, start, end, ortools_time_limit=2)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == start
    assert path[-1] == end
    assert set(path) == {0, 1, 2}
    expected = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isclose(L, expected)

if __name__ == "__main__":
    test_case_A_basic_fixed_start_end()
    test_case_B_different_fixed_endpoints()
    test_case_C_single_possible_path()
    test_case_D_start_equals_end()