import numpy as np
import numbers
from libraries.utils.algorithm.single_route.coverage_cost import compute_rute_covarage

def test_case_1_scalar_E():
    """
    Basic case: E is a scalar. DG = E * sum(p) - APR * L_R
    """
    print("\n=== TEST CASE 1: Scalar E ===")
    E = 5.0
    APR = 0.2
    p = [1, 2, 3]      # sum = 6
    L_R = 10.0
    DG = compute_rute_covarage(E, APR, p, L_R)
    expected = 5.0 * 6 - 0.2 * 10   # = 30 - 2 = 28
    print("DG =", DG)
    assert np.isclose(DG, expected)
    assert isinstance(DG, numbers.Real)

def test_case_2_vector_E():
    """
    Vector-valued revenue: DG = sum(E[i] * p[i]) - APR * L_R
    """
    print("\n=== TEST CASE 2: Vector E ===")
    E = [2.0, 5.0, 3.0]
    APR = 1.0
    p = [1, 2, 3]
    L_R = 10.0
    expected = 21 - 1*10  # = 11
    DG = compute_rute_covarage(E, APR, p, L_R)
    print("DG =", DG)
    assert np.isclose(DG, expected)
    assert isinstance(DG, numbers.Real)

def test_case_3_vector_E_reproducible():
    """
    Reproducibility test: vector E with random generation upstream should always give same DG for same E and p.
    """
    print("\n=== TEST CASE 3: Reproducibility ===")
    rng = np.random.default_rng(123)
    E = np.maximum(5 + rng.uniform(-2, 2, size=5), 0)
    APR = 0.5
    p = [1, 1, 1, 1, 1]
    L_R = 20.0
    DG1 = compute_rute_covarage(E, APR, p, L_R)
    DG2 = compute_rute_covarage(E, APR, p, L_R)
    print("DG1 =", DG1)
    print("DG2 =", DG2)
    assert np.isclose(DG1, DG2)

def test_case_4_invalid_E_length():
    """
    Length of E must match p when E is vector-valued.
    """
    print("\n=== TEST CASE 4: Invalid E-vector length raises error ===")
    E = [1.0, 2.0]   
    APR = 1.0
    p = [1, 2, 3]    
    L_R = 5.0
    error_raised = False
    try:
        compute_rute_covarage(E, APR, p, L_R)
    except ValueError as er:
        print(f"Error correctly raised: {er}")
        error_raised = True
    assert error_raised, "Expected ValueError when E and p lengths mismatch"

def test_case_5_empty_route():
    """
    Edge case: empty p-vector. DG should be -APR * L_R.
    """
    print("\n=== TEST CASE 5: Empty route ===")
    E = 5.0
    APR = 0.2
    p = []
    L_R = 10.0
    DG = compute_rute_covarage(E, APR, p, L_R)
    expected = -0.2 * 10  
    print("DG =", DG)
    assert np.isclose(DG, expected)

if __name__ == "__main__":
    test_case_1_scalar_E()
    test_case_2_vector_E()
    test_case_3_vector_E_reproducible()
    test_case_4_invalid_E_length()
    test_case_5_empty_route()