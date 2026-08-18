import numpy as np
from libraries.utils.algorithm.solvers.tsp import tsp_solve
from libraries.utils.experiments.simulations import simulate_addresses

def test_case_A_small_symmetric():
    """
    Deterministic test using the GREEDY solver.
    """
    print("\n=== CASE A: Small symmetric TSP (Greedy) ===")
    D = np.array([
        [0, 1, 9],
        [1, 0, 8],
        [9, 8, 0],
    ])
    route_order, L = tsp_solve(D, deterministic_tsp=True, solver="greedy")
    print("Route:", route_order)
    print("Length:", L)
    # Expected: 0→1→2→0 = 1 + 8 + 9 = 18 OR symmetric variant 1→0→2→1
    expected_length = 1 + 8 + 9
    assert np.isclose(L, expected_length)
    assert sorted(route_order) == [0, 1, 2]

def test_case_B_simulated_fk():
    """
    Test both deterministic (OR-Tools) and stochastic (python_tsp) solvers
    on a simulated asymmetric FK-like network.
    """
    print("\n=== CASE B: Simulated FK network ===")
    n = 10
    seed = 834
    D, _ = simulate_addresses(
        n=n,
        seed=seed,
        asymmetry_strength=0.2,
        outlier_fraction=0.1
    )
    # -----------------------------
    # Deterministic solver: Greedy
    # -----------------------------
    r_greedy1, L_greedy1 = tsp_solve(D, deterministic_tsp=True, solver="greedy")
    r_greedy2, L_greedy2 = tsp_solve(D, deterministic_tsp=True, solver="greedy")
    print("Greedy route 1:", r_greedy1, " length:", L_greedy1)
    print("Greedy route 2:", r_greedy2, " length:", L_greedy2)
    assert len(r_greedy1) == n
    assert sorted(r_greedy1) == list(range(n))
    assert r_greedy1 == r_greedy2
    assert np.isclose(L_greedy1, L_greedy2)
    assert L_greedy1 > 0
    assert np.isfinite(L_greedy1)

    # -----------------------------
    # Deterministic solver: OR-Tools
    # -----------------------------
    r_det1, L_det1 = tsp_solve(D, deterministic_tsp=True, solver="ortools")
    r_det2, L_det2 = tsp_solve(D, deterministic_tsp=True, solver="ortools")
    print("Deterministic route 1:", r_det1, " length:", L_det1)
    print("Deterministic route 2:", r_det2, " length:", L_det2)
    assert len(r_det1) == n
    assert sorted(r_det1) == list(range(n))
    assert r_det1 == r_det2
    assert np.isclose(L_det1, L_det2)
    assert L_det1 > 0
    assert np.isfinite(L_det1)
    # -----------------------------------------------------
    # Deterministic solver: LKH (via ELKAI)
    # -----------------------------------------------------
    r_l1, L_l1 = tsp_solve(D, deterministic_tsp=True, solver="lkh")
    r_l2, L_l2 = tsp_solve(D, deterministic_tsp=True, solver="lkh")
    print("LKH/ELKAI route 1:", r_l1, "length:", L_l1)
    print("LKH/ELKAI route 2:", r_l2, "length:", L_l2)
    assert sorted(r_l1) == list(range(len(D)))
    assert sorted(r_l2) == list(range(len(D)))
    assert np.isclose(L_l1, L_l2, atol=1e-6)

    # -----------------------------
    # Stochastic solver: python_tsp
    # -----------------------------
    r_st1, L_st1 = tsp_solve(D, deterministic_tsp=False, solver="python_tsp")
    r_st2, L_st2 = tsp_solve(D, deterministic_tsp=False, solver="python_tsp")
    print("Stochastic route 1:", r_st1, " length:", L_st1)
    print("Stochastic route 2:", r_st2, " length:", L_st2)
    assert len(r_st1) == len(r_st2)
    assert sorted(r_st1) == sorted(r_st2)
    assert L_st1 > 0 and L_st2 > 0
    assert np.isfinite(L_st1) and np.isfinite(L_st2)

def test_case_C_deterministic_vs_random():
    """
    Compares deterministic solvers (greedy, OR-Tools, LKH/ELKAI)
    vs stochastic solver (python_tsp).
    """
    print("\n=== CASE C: Deterministic vs Random TSP ===")
    D = np.array([
        [0, 2, 9, 10],
        [1, 0, 6,  4],
        [15,6, 0,  8],
        [6,  3,12, 0]
    ], dtype=float)

    # -----------------------------------------------------
    # Deterministic solver: Greedy
    # -----------------------------------------------------
    r_g1, L_g1 = tsp_solve(D, deterministic_tsp=True, solver="greedy")
    r_g2, L_g2 = tsp_solve(D, deterministic_tsp=True, solver="greedy")
    print("Greedy route 1:", r_g1, "length:", L_g1)
    print("Greedy route 2:", r_g2, "length:", L_g2)
    assert r_g1 == r_g2
    assert np.isclose(L_g1, L_g2)

    # -----------------------------------------------------
    # Deterministic solver: OR-Tools
    # -----------------------------------------------------
    r_o1, L_o1 = tsp_solve(D, deterministic_tsp=True, solver="ortools")
    r_o2, L_o2 = tsp_solve(D, deterministic_tsp=True, solver="ortools")
    print("OR-Tools route 1:", r_o1, "length:", L_o1)
    print("OR-Tools route 2:", r_o2, "length:", L_o2)
    assert r_o1 == r_o2
    assert np.isclose(L_o1, L_o2)

    # -----------------------------------------------------
    # Deterministic solver: LKH (via ELKAI)
    # -----------------------------------------------------
    r_l1, L_l1 = tsp_solve(D, deterministic_tsp=True, solver="lkh")
    r_l2, L_l2 = tsp_solve(D, deterministic_tsp=True, solver="lkh")
    print("LKH/ELKAI route 1:", r_l1, "length:", L_l1)
    print("LKH/ELKAI route 2:", r_l2, "length:", L_l2)
    assert sorted(r_l1) == list(range(len(D)))
    assert sorted(r_l2) == list(range(len(D)))
    assert np.isclose(L_l1, L_l2, atol=1e-6)

    # -----------------------------------------------------
    # Stochastic solver: python_tsp
    # -----------------------------------------------------
    r_p1, L_p1 = tsp_solve(D, deterministic_tsp=False, solver="python_tsp")
    r_p2, L_p2 = tsp_solve(D, deterministic_tsp=False, solver="python_tsp")
    print("python_tsp route 1:", r_p1, "length:", L_p1)
    print("python_tsp route 2:", r_p2, "length:", L_p2)
    assert len(r_p1) == len(r_p2)
    assert sorted(r_p1) == sorted(r_p2)
    assert L_p1 > 0 and L_p2 > 0
    assert np.isfinite(L_p1) and np.isfinite(L_p2)

if __name__ == "__main__":
    test_case_A_small_symmetric()
    test_case_B_simulated_fk()
    test_case_C_deterministic_vs_random()
