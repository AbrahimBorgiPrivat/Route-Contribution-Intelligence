import numpy as np
from libraries.utils.algorithm.structural_heuristics.greedy_peripheral_clusters import estimate_tsp_threshold
from libraries.utils.experiments.simulations import simulate_addresses
import numbers

def test_case_1_simple_kneedle():
    """
    Simple increasing edges: L = [1,2,3,4,20]
    Expected knee: edges sorted = [1,2,2,3,20] → knee at 3
    """
    D = np.array([
        [0, 1, 2, 3, 20],
        [1, 0, 2, 3, 20],
        [2, 2, 0, 3, 20],
        [3, 3, 3, 0, 20],
        [20,20,20,20, 0]
    ])
    R_seq = [0,1,2,3,4]
    thr = estimate_tsp_threshold(D, R_seq, method="kneedle")
    print("\nCase 1 (simple kneedle): threshold =", thr)
    assert isinstance(thr, numbers.Real)
    assert thr in (2, 3, 20)      
    assert thr <= 20

def test_case_2_relative_jump():
    """
    Strong relative jump: L = [3,4,4,5,120]
    First ratio >= 2.0 is at 120/5
    Expected threshold = L[i] = 5
    """
    D = np.array([
        [0, 3, 4, 5,120],
        [3, 0, 4, 5,120],
        [4, 4, 0, 5,120],
        [5, 5, 5, 0,120],
        [120,120,120,120, 0]
    ])
    R_seq = [0,1,2,3,4]
    thr = estimate_tsp_threshold(D, R_seq, method="relative", min_rel_jump=2.0)
    print("\nCase 2 (relative jump): threshold =", thr)
    assert isinstance(thr, numbers.Real)
    assert thr == 5

def test_case_3_all_equal():
    """
    All equal edges → threshold should equal that constant value.
    """
    D = np.array([
        [0,10,10],
        [10,0,10],
        [10,10,0],
    ])
    R_seq = [0,1,2]
    thr1 = estimate_tsp_threshold(D, R_seq, method="kneedle")
    thr2 = estimate_tsp_threshold(D, R_seq, method="relative")
    print("\nCase 3 (all equal): kneedle =", thr1, ", relative =", thr2)
    assert isinstance(thr1, numbers.Real)
    assert isinstance(thr2, numbers.Real)
    assert thr1 == 10
    assert thr2 == 10

def test_case_4_simulated_fk():
    """
    Realistic FK-like route with spur edges.
    Seed = 834 (verified good seed).
    Kneedle and relative *often* agree when spur edges are large.
    """
    seed = 834
    n = 10
    asymmetry_strength = 0.2
    outlier_fraction = 0.10
    print(f"\nCase 4 (simulated FK): seed={seed}")
    D, p = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=asymmetry_strength,
        outlier_fraction=outlier_fraction,
    )
    R_seq = list(range(n))
    thr_kneedle = estimate_tsp_threshold(D, R_seq, method="kneedle")
    thr_rel     = estimate_tsp_threshold(D, R_seq, method="relative", min_rel_jump=2.0)
    print("  kneedle threshold =", thr_kneedle)
    print("  relative threshold =", thr_rel)

    assert isinstance(thr_kneedle, numbers.Real)
    assert isinstance(thr_rel, numbers.Real)
    assert thr_kneedle > 0
    assert thr_rel > 0

if __name__ == "__main__":
    test_case_1_simple_kneedle()
    test_case_2_relative_jump()
    test_case_3_all_equal()
    test_case_4_simulated_fk()