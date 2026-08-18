import numpy as np
from libraries.utils.algorithm.solvers.hpp import hpp_solve
from libraries.utils.experiments.simulations import simulate_addresses


def assert_valid_hpp(path, D):
    """
    Common contract checks for HPP solutions.
    """
    n = len(D)
    assert isinstance(path, list)
    assert len(path) == n
    assert sorted(path) == list(range(n))
    L = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    assert np.isfinite(L)
    assert L > 0

def test_case_A_small_symmetric_greedy():
    """
    Deterministic test using greedy DENN.
    """
    print("\n=== CASE A: Small symmetric HPP (Greedy) ===")
    D = np.array([
        [0, 1, 9],
        [1, 0, 8],
        [9, 8, 0],
    ], dtype=float)
    path, L = hpp_solve(D, solver="greedy")
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_B_small_symmetric_ortools():
    """
    OR-Tools HPP with default GREEDY_DNN initialisation.
    """
    print("\n=== CASE B: Small symmetric HPP (OR-Tools) ===")
    D = np.array([
        [0, 1, 9],
        [1, 0, 8],
        [9, 8, 0],
    ], dtype=float)
    path, L = hpp_solve(D, solver="ortools")
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_C_fixed_start_end():
    """
    Fixed endpoints should bypass candidate logic and solve once.
    """
    print("\n=== CASE C: Fixed start/end ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [7, 3, 0, 8],
        [6, 5, 12, 0],
    ], dtype=float)
    fixed = {"start": 0, "end": 3}
    path, L = hpp_solve(D, solver="ortools", fixed_endpoints=fixed)
    print("Path:", path)
    print("Length:", L)
    assert path[0] == 0
    assert path[-1] == 3
    assert_valid_hpp(path, D)

def test_case_D_simulated_fk():
    """
    Compare greedy DENN and OR-Tools on FK-like asymmetric data.
    """
    print("\n=== CASE D: Simulated FK network ===")
    n = 12
    seed = 421
    D, _ = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.25,
        outlier_fraction=0.1,
    )
    r_g1, L_g1 = hpp_solve(D, solver="greedy_denn")
    r_g2, L_g2 = hpp_solve(D, solver="greedy_denn")
    print("Greedy route 1:", r_g1, "length:", L_g1)
    print("Greedy route 2:", r_g2, "length:", L_g2)
    assert r_g1 == r_g2
    assert np.isclose(L_g1, L_g2)
    assert_valid_hpp(r_g1, D)
    r_o1, L_o1 = hpp_solve(D, solver="ortools")
    r_o2, L_o2 = hpp_solve(D, solver="ortools")
    print("OR-Tools route 1:", r_o1, "length:", L_o1)
    print("OR-Tools route 2:", r_o2, "length:", L_o2)
    assert r_o1 == r_o2
    assert np.isclose(L_o1, L_o2)
    assert_valid_hpp(r_o1, D)

def test_case_E_extended_search():
    """
    OR-Tools with EXTENDED_SEARCH initialisation.
    """
    print("\n=== CASE E: EXTENDED_SEARCH ===")
    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ], dtype=float)
    method = {"method": "EXTENDED_SEARCH", "n_iterations": 2}
    path, L = hpp_solve(
        D,
        solver="ortools",
        initial_point_method=method,
    )
    print("Path:", path)
    print("Length:", L)
    assert_valid_hpp(path, D)

def test_case_F_invalid_solver():
    """
    Invalid solver name should raise ValueError.
    """
    print("\n=== CASE F: Invalid solver ===")
    D = np.array([
        [0, 1],
        [1, 0],
    ], dtype=float)
    try:
        _ = hpp_solve(D, solver="not_a_solver")
        assert False
    except ValueError as e:
        print("Correctly caught ValueError:", e)

def test_case_G_cheapest_insertion_solver():
    """
    PyVRP solver should work for free HPP (no fixed endpoints).
    """
    print("\n=== CASE G: Valid solver cheapest_insertion ===")
    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    path, L = hpp_solve(
        D,
        solver="cheapest_insertion",
        fixed_endpoints=None,
    )
    print("Route:", path)
    print("Length:", L)
    assert isinstance(path, list)
    assert len(path) == len(D)
    assert sorted(path) == list(range(len(D)))
    assert isinstance(L, (int, float))
    assert np.isfinite(L)
    assert L > 0

if __name__ == "__main__":
    test_case_A_small_symmetric_greedy()
    test_case_B_small_symmetric_ortools()
    test_case_C_fixed_start_end()
    test_case_D_simulated_fk()
    test_case_E_extended_search()
    test_case_F_invalid_solver()
    test_case_G_cheapest_insertion_solver()