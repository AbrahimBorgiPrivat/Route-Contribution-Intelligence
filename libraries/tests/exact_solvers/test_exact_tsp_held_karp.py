import numbers
import itertools
import numpy as np
from libraries.utils.algorithm.solvers.exact_solvers import exact_tsp_held_karp
from libraries.utils.experiments.simulations import simulate_addresses

def _assert_valid_tsp(route, L, D):
    n = len(D)
    assert isinstance(route, list)
    assert isinstance(L, numbers.Real)
    assert L >= 0
    assert len(route) == n
    assert set(route) == set(range(n))
    calc_L = sum(
        D[route[i], route[(i + 1) % n]]
        for i in range(n)
    )
    assert np.isclose(L, calc_L)

def _bruteforce_tsp(D):
    """
    Exact brute-force TSP solver for small n.
    Fixes start node to 0 to avoid equivalent rotations.
    """
    n = len(D)
    best_L = np.inf
    best_route = None
    for perm in itertools.permutations(range(1, n)):
        route = [0] + list(perm)
        L = sum(D[route[i], route[(i + 1) % n]] for i in range(n))
        if L < best_L:
            best_L = L
            best_route = route
    return best_route, best_L

# ==================================================
# TEST 1: Small symmetric matrix (known optimum)
# ==================================================
def test_exact_tsp_small_symmetric():
    print("\n=== EXACT TSP: Small symmetric ===")
    D = np.array([
        [0, 2, 9],
        [2, 0, 8],
        [9, 8, 0],
    ], dtype=float)
    route, L = exact_tsp_held_karp(D)
    bf_route, bf_L = _bruteforce_tsp(D)
    print("Held–Karp:", route, L)
    print("Bruteforce:", bf_route, bf_L)
    _assert_valid_tsp(route, L, D)
    assert np.isclose(L, bf_L)

# ==================================================
# TEST 2: Asymmetric matrix (exact optimality)
# ==================================================
def test_exact_tsp_asymmetric():
    print("\n=== EXACT TSP: Asymmetric matrix ===")

    D = np.array([
        [0, 3, 4, 2],
        [2, 0, 6, 3],
        [7, 5, 0, 8],
        [3, 4, 1, 0],
    ], dtype=float)
    route, L = exact_tsp_held_karp(D)
    bf_route, bf_L = _bruteforce_tsp(D)
    print("Held–Karp:", route, L)
    print("Bruteforce:", bf_route, bf_L)
    _assert_valid_tsp(route, L, D)
    assert np.isclose(L, bf_L)

def test_exact_tsp_simulated_fk():
    """
    Deterministic FK-style test using simulate_addresses().
    Ensures exact TSP returns a valid tour and finite optimal length.
    """
    print("\n=== EXACT TSP: Simulated FK addresses (seed=834) ===")

    n = 10  # keep n modest due to exponential complexity
    seed = 834

    D, _ = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.2,
        outlier_fraction=0.1,
    )

    route, L = exact_tsp_held_karp(D)

    print("Route:", route)
    print("Length:", L)

    assert len(route) == n
    assert sorted(route) == list(range(n))
    assert L > 0
    assert np.isfinite(L)

if __name__ == "__main__":
    test_exact_tsp_small_symmetric()
    test_exact_tsp_asymmetric()
    test_exact_tsp_simulated_fk()
