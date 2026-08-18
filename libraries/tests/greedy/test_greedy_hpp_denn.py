import numpy as np
from libraries.utils.algorithm.solvers.greedy import greedy_hpp_denn

def test_case_A_free_HPP():
    print("\n=== CASE A: Free HPP (no fixed endpoints) ===")
    D = np.array([
        [0, 2, 9],
        [1, 0, 6],
        [7, 3, 0],
    ])
    path, L = greedy_hpp_denn(D)
    print("Path:", path)
    print("Length:", L)
    assert sorted(path) == [0, 1, 2]
    expected = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isclose(L, expected)


def test_case_B_fixed_start():
    print("\n=== CASE B: Fixed start ===")
    D = np.array([
        [0, 2, 9],
        [1, 0, 6],
        [7, 3, 0],
    ])
    fixed = {"start": 0, "end": None}
    path, L = greedy_hpp_denn(D, fixed_endpoints=fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert sorted(path) == [0, 1, 2]


def test_case_C_fixed_end():
    print("\n=== CASE C: Fixed end ===")
    D = np.array([
        [0, 2, 9],
        [1, 0, 6],
        [7, 3, 0],
    ])
    fixed = {"start": None, "end": 2}
    path, L = greedy_hpp_denn(D, fixed_endpoints=fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[-1] == 2
    assert sorted(path) == [0, 1, 2]


def test_case_D_fixed_start_and_end():
    print("\n=== CASE D: Fixed start and end ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    fixed = {"start": 0, "end": 3}
    path, L = greedy_hpp_denn(D, fixed_endpoints=fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert path[-1] == 3
    assert sorted(path) == [0, 1, 2, 3]


def test_case_E_determinism():
    print("\n=== CASE E: Determinism check ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ])
    path1, L1 = greedy_hpp_denn(D)
    path2, L2 = greedy_hpp_denn(D)
    print("Run 1:", path1, L1)
    print("Run 2:", path2, L2)
    assert path1 == path2
    assert np.isclose(L1, L2)


def test_case_F_invalid_fixed_endpoints():
    print("\n=== CASE F: Invalid fixed endpoints ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ])
    fixed = {"start": 0, "end": 0}
    try:
        _ = greedy_hpp_denn(D, fixed_endpoints=fixed)
        print("ERROR: Expected failure but function succeeded.")
        assert False
    except ValueError as e:
        print("Correctly caught ValueError:", e)


if __name__ == "__main__":
    test_case_A_free_HPP()
    test_case_B_fixed_start()
    test_case_C_fixed_end()
    test_case_D_fixed_start_and_end()
    test_case_E_determinism()
    test_case_F_invalid_fixed_endpoints()