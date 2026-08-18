import numpy as np
from libraries.utils.algorithm.solvers.greedy import greedy_tsp_algorithm
from libraries.utils.experiments.simulations import simulate_addresses

def test_case_1_small_symmetric():
    """
    Very small symmetric case:
    Best tour is known and easy to compute manually.
    """
    print("\n=== GREEDY CASE 1: Small symmetric ===")
    D = np.array([
        [0, 2, 9],
        [2, 0, 8],
        [9, 8, 0],
    ])
    route, L = greedy_tsp_algorithm(D)
    print("Route:", route)
    print("Length:", L)
    assert np.isclose(L, 19)
    assert len(route) == 3
    assert all(isinstance(x, (int, np.integer)) for x in route)


def test_case_2_asymmetric_matrix():
    """
    Greedy should still return a valid permutation even for asymmetric matrices.
    """
    print("\n=== GREEDY CASE 2: Asymmetric matrix ===")
    D = np.array([
        [0, 3, 4, 2],
        [2, 0, 6, 3],
        [7, 5, 0, 8],
        [3, 4, 1, 0],
    ])
    route, L = greedy_tsp_algorithm(D)
    print("Route:", route)
    print("Length:", L)
    assert len(route) == 4
    assert sorted(route) == [0, 1, 2, 3]
    assert L > 0

def test_case_3_deterministic_behavior():
    """
    Greedy is 100% deterministic.
    Running it twice with the same D should give identical routes and lengths.
    """
    print("\n=== GREEDY CASE 3: Deterministic behavior ===")
    D = np.array([
        [0, 4, 1, 9],
        [4, 0, 3, 8],
        [1, 3, 0, 6],
        [9, 8, 6, 0],
    ])
    r1, L1 = greedy_tsp_algorithm(D)
    r2, L2 = greedy_tsp_algorithm(D)
    print("Route 1:", r1, " Length:", L1)
    print("Route 2:", r2, " Length:", L2)
    assert r1 == r2
    assert np.isclose(L1, L2)

def test_case_4_simulated_fk():
    """
    Deterministic FK-style test using simulate_addresses().
    Ensures greedy returns a valid route and finite length.
    """
    print("\n=== GREEDY CASE 4: Simulated FK addresses (seed=834) ===")
    n = 12
    seed = 834
    D, _ = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.2,
        outlier_fraction=0.1
    )
    route, L = greedy_tsp_algorithm(D)
    print("Route:", route)
    print("Length:", L)
    assert len(route) == n
    assert sorted(route) == list(range(n))
    assert L > 0
    assert np.isfinite(L)

if __name__ == "__main__":
    test_case_1_small_symmetric()
    test_case_2_asymmetric_matrix()
    test_case_3_deterministic_behavior()
    test_case_4_simulated_fk()
