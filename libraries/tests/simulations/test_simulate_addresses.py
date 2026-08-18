import numpy as np
from libraries.utils.experiments.simulations import simulate_addresses

def print_matrix(D):
    """Helper function to print matrices in a readable form."""
    with np.printoptions(precision=3, suppress=True):
        print(D)

def test_case_1_basic():
    """
    Basic test: small n, no asymmetry, no outliers.
    Distances should be symmetric and reasonable.
    """
    print("\n=== TEST CASE 1: Basic simulation (n=5) ===")
    n = 5
    seed = 42
    D, p = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0,
        outlier_fraction=0.0,
        min_postboxes=1,
        max_postboxes=5,
    )
    print("Distance matrix (symmetric expected):")
    print_matrix(D)
    print("Postboxes:", p)
    assert D.shape == (n, n)
    assert p.shape == (n,)
    assert np.allclose(D, D.T)   
    assert np.all(p >= 1) and np.all(p <= 5)

def test_case_2_asymmetric():
    """
    Asymmetry test: D[i,j] != D[j,i] often.
    """
    print("\n=== TEST CASE 2: Asymmetric simulation (n=6) ===")
    n = 6
    seed = 123
    D, p = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.5,   
        outlier_fraction=0.0,
    )
    print("Distance matrix (asymmetric expected):")
    print_matrix(D)
    asym_fraction = np.mean(~np.isclose(D, D.T))
    print("Fraction of asymmetric pairs:", asym_fraction)
    assert D.shape == (n, n)
    assert asym_fraction > 0.1  

def test_case_3_outliers():
    """
    Outlier test: with outlier_fraction > 0, first nodes should be far away.
    """
    print("\n=== TEST CASE 3: Outlier simulation (n=10) ===")
    n = 10
    seed = 834
    outlier_fraction = 0.20
    asymmetry_strength = 0.2

    D, p = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=asymmetry_strength,
        outlier_fraction=outlier_fraction,
        min_postboxes=1,
        max_postboxes=10,
    )
    print("Distance matrix:")
    print_matrix(D)
    print("Postboxes:", p)
    expected_outliers = max(1, int(n * outlier_fraction))
    print(f"Expected outliers: {expected_outliers}")
    distances_from_first_outlier = D[0]
    median_dist = np.median(D[D > 0])
    print("Median distance:", median_dist)
    print("Distances from node 0:", distances_from_first_outlier)
    assert p[0] >= 2 and p[0] <= 10   

def test_case_4_random_reproducible():
    """
    Reproducibility test: same seed → same result.
    """
    print("\n=== TEST CASE 4: Reproducibility (n=8, seed=999) ===")
    n = 8
    seed = 999
    D1, p1 = simulate_addresses(n=n, seed=seed, asymmetry_strength=0.1)
    D2, p2 = simulate_addresses(n=n, seed=seed, asymmetry_strength=0.1)
    print("D1:")
    print_matrix(D1)
    print("p1:", p1)
    print("D2:")
    print_matrix(D2)
    print("p2:", p2)
    assert np.allclose(D1, D2)
    assert np.array_equal(p1, p2)

def test_case_5_vector_E_output():
    """
    When E is a dict → simulate_addresses must return (D, p, E_vec).
    """
    print("\n=== TEST CASE 5: Vector-valued E generation ===")
    n = 6
    seed = 123
    E_cfg = {
        "val": 5.0,
        "deviation": 2.0,
        "seed": 777
    }
    D, p, E_vec1 = simulate_addresses(
        n=n, seed=seed, asymmetry_strength=0.1, E=E_cfg
    )
    D, p, E_vec2 = simulate_addresses(
        n=n, seed=seed, asymmetry_strength=0.1, E=E_cfg
    )
    print("E_vec1:", E_vec1)
    print("E_vec2:", E_vec2)
    assert len(E_vec1) == n
    assert len(E_vec2) == n
    assert np.all(E_vec1 >= 0)
    assert np.allclose(E_vec1, E_vec2)
    assert D.shape == (n, n)
    assert len(p) == n


def test_case_6_invalid_E_raises_error():
    """
    E dict must contain at least 'val' and 'deviation'. Missing keys → should raise ValueError.
    """
    print("\n=== TEST CASE 6: Invalid E dict raises error ===")
    n = 5
    seed = 42
    bad_E_cfg = {
        "val": 5.0
    }
    error_raised = False
    try:
        simulate_addresses(
            n=n, seed=seed, asymmetry_strength=0.1, E=bad_E_cfg
        )
    except ValueError as ve:
        print(f"ValueError correctly raised for invalid E config: {ve}")
        error_raised = True
    print("Error raised:", error_raised)
    assert error_raised

if __name__ == "__main__":
    test_case_1_basic()
    test_case_2_asymmetric()
    test_case_3_outliers()
    test_case_4_random_reproducible()
    test_case_5_vector_E_output()
    test_case_6_invalid_E_raises_error()
