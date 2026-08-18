import numbers
import itertools
import numpy as np
from libraries.utils.algorithm.solvers.exact_solvers import exact_hpp_held_karp
from libraries.utils.experiments.simulations import simulate_addresses

def _assert_valid_hpp(path, L, D):
    n = len(D)
    assert isinstance(path, list)
    assert isinstance(L, numbers.Real)
    assert L >= 0
    assert set(path) == set(range(n))
    assert len(path) == n
    calc_L = sum(D[path[i], path[i + 1]] for i in range(n - 1))
    assert np.isclose(L, calc_L)

def _bruteforce_hpp(D, start=None, end=None):
    """
    Brute-force Hamiltonian Path (exact) for validation.
    Used only for very small n.
    """
    n = len(D)
    best_L = np.inf
    best_path = None
    for perm in itertools.permutations(range(n)):
        if start is not None and perm[0] != start:
            continue
        if end is not None and perm[-1] != end:
            continue

        L = sum(D[perm[i], perm[i + 1]] for i in range(n - 1))
        if L < best_L:
            best_L = L
            best_path = list(perm)
    return best_path, best_L


# ==================================================
# TEST 1: Free HPP — exact optimality
# ==================================================
def test_exact_hpp_free_matches_bruteforce():
    print("\n=== EXACT HPP: Free endpoints ===")

    D = np.array([
        [0, 2, 9, 7],
        [1, 0, 3, 4],
        [4, 3, 0, 5],
        [6, 5, 1, 0],
    ], dtype=float)
    path, L = exact_hpp_held_karp(D)
    bf_path, bf_L = _bruteforce_hpp(D)
    print("Held–Karp:", path, L)
    print("Bruteforce:", bf_path, bf_L)
    _assert_valid_hpp(path, L, D)
    assert np.isclose(L, bf_L)

# ==================================================
# TEST 2: Fixed start & end — exact optimality
# ==================================================
def test_exact_hpp_fixed_start_end_matches_bruteforce():
    print("\n=== EXACT HPP: Fixed start & end ===")
    D = np.array([
        [0, 3, 8, 2],
        [3, 0, 4, 7],
        [8, 4, 0, 6],
        [2, 7, 6, 0],
    ], dtype=float)

    fixed = {"start": 0, "end": 3}
    path, L = exact_hpp_held_karp(D, fixed_endpoints=fixed)
    bf_path, bf_L = _bruteforce_hpp(D, start=0, end=3)
    print("Held–Karp:", path, L)
    print("Bruteforce:", bf_path, bf_L)
    assert path[0] == 0
    assert path[-1] == 3
    _assert_valid_hpp(path, L, D)
    assert np.isclose(L, bf_L)

def test_exact_hpp_simulated_fk():
    """
    Deterministic FK-style test using simulate_addresses().
    Ensures exact HPP returns a valid path and finite optimal length.
    """
    print("\n=== EXACT HPP: Simulated FK addresses (seed=834) ===")
    n = 10  
    seed = 834
    D, _ = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.2,
        outlier_fraction=0.1,
    )
    path, L = exact_hpp_held_karp(D)
    print("Path:", path)
    print("Length:", L)
    assert len(path) == n
    assert sorted(path) == list(range(n))
    assert L >= 0
    assert np.isfinite(L)

if __name__ == "__main__":
    test_exact_hpp_free_matches_bruteforce()
    test_exact_hpp_fixed_start_end_matches_bruteforce()
    test_exact_hpp_simulated_fk()