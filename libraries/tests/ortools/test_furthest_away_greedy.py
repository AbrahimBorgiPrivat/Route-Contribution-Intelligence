import numpy as np
import pytest
from libraries.utils.algorithm.solvers.ortools import furthest_away_greedy

def test_case_A_basic_n_edges_1():
    print("\n=== CASE A: n_edges = 1 (direct distance) ===")
    D = np.array([
        [0, 1, 5],
        [1, 0, 2],
        [5, 2, 0],
    ])
    (s, e), L = furthest_away_greedy(D, n_edges=1)
    print("Selected:", (s, e), "Length:", L)
    assert {s, e} == {0, 2}
    assert np.isclose(L, 5.0)


def test_case_B_n_edges_2():
    print("\n=== CASE B: n_edges = 2 ===")
    D = np.array([
        [0, 1, 5, 9],
        [1, 0, 2, 4],
        [5, 2, 0, 3],
        [9, 4, 3, 0],
    ])
    (s, e), L = furthest_away_greedy(D, n_edges=2)
    print("Selected:", (s, e), "Length:", L)
    assert s != e
    assert 0 <= s < 4
    assert 0 <= e < 4
    assert L > 0


def test_case_C_fixed_start():
    print("\n=== CASE C: Fixed start ===")
    D = np.array([
        [0, 1, 5],
        [1, 0, 2],
        [5, 2, 0],
    ])
    (s, e), L = furthest_away_greedy(D, n_edges=2, start_fixed=0)
    print("Selected:", (s, e), "Length:", L)
    assert s == 0
    assert e != 0


def test_case_D_fixed_end():
    print("\n=== CASE D: Fixed end ===")
    D = np.array([
        [0, 1, 5],
        [1, 0, 2],
        [5, 2, 0],
    ])
    (s, e), L = furthest_away_greedy(D, n_edges=2, end_fixed=2)
    print("Selected:", (s, e), "Length:", L)
    assert e == 2
    assert s != 2


def test_case_E_fixed_start_and_end():
    print("\n=== CASE E: Fixed start and end ===")
    D = np.array([
        [0, 1, 5, 9],
        [1, 0, 2, 4],
        [5, 2, 0, 3],
        [9, 4, 3, 0],
    ])
    (s, e), L = furthest_away_greedy(
        D,
        n_edges=2,
        start_fixed=0,
        end_fixed=3,
    )
    print("Selected:", (s, e), "Length:", L)
    assert s == 0
    assert e == 3

def test_case_F_invalid_n_edges():
    print("\n=== CASE F: Invalid n_edges ===")
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ])
    with pytest.raises(ValueError, match="n_edges must be < number of nodes"):
        _ = furthest_away_greedy(D, n_edges=3)


if __name__ == "__main__":
    test_case_A_basic_n_edges_1()
    test_case_B_n_edges_2()
    test_case_C_fixed_start()
    test_case_D_fixed_end()
    test_case_E_fixed_start_and_end()
    test_case_F_invalid_n_edges()