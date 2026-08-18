import numpy as np
from libraries.utils.algorithm.single_route.coverage_cost import compute_coverage_change
import numbers

def test_case_1_remove_nothing():
    """
    Removing S = {} changes only distance:
    C2 = -APR * C
    """
    print("\n=== CASE 1: Remove nothing ===")
    E = 5.0
    APR = 0.1
    p = [2, 3, 4]
    R = [0, 1, 2]
    S = set()
    C = +10.0   
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)
    expected = -APR * C
    assert np.isclose(C2, expected)
    assert isinstance(C2, numbers.Real)

def test_case_2_remove_one():
    """
    Removing one node reduces postboxes:
    C2 = E*(new_postboxes - old_postboxes) - APR*C
    """
    print("\n=== CASE 2: Remove one node ===")
    E = 5.0
    APR = 0.2
    p = [2, 10, 3]    
    R = [0, 1, 2]
    S = {1}           
    C = -4.0          
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)
    old = 15
    new = p[0] + p[2]   # = 5
    expected = E*(new - old) - APR*C  
    assert np.isclose(C2, expected)
    assert isinstance(C2, numbers.Real)

def test_case_3_remove_two():
    """
    Remove multiple nodes, positive C effect.
    """
    print("\n=== CASE 3: Remove two nodes ===")
    E = 1.0
    APR = 1.0
    p = [1, 10, 20, 3]   
    R = [0, 1, 2, 3]
    S = {1, 2}
    C = -5.0  
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)
    expected = 1*(4 - 34) - 1*(-5)  # = -30 + 5 = -25
    assert np.isclose(C2, expected)
    assert isinstance(C2, numbers.Real)

def test_case_4_remove_all():
    """
    Remove multiple nodes, positive C effect.
    """
    print("\n=== CASE 4: Remove all nodes ===")
    E = 2.0
    APR = 0.5
    p = [3, 3]
    R = [0, 1]
    S = {0, 1}
    C = -100.0
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)
    expected = 2*(0 - 6) - 0.5*(-100)  # -12 + 50 = 38
    assert np.isclose(C2, expected)
    assert isinstance(C2, numbers.Real)

def test_case_5_remove_one_increases_coverage():
    """
    Removing one node INCREASES coverage (C2 > 0):
    """
    print("\n=== CASE 5: Removal increases coverage ===")
    E = 1.0
    APR = 1.0
    p = [10, 1, 10] 
    R = [0, 1, 2]
    S = {1}
    C = -50.0  
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)
    old = 21 
    new = 20
    expected = E*(new - old) - APR*C 
    assert np.isclose(C2, expected)
    assert C2 > 0
    assert isinstance(C2, numbers.Real)

def test_case_6_vector_E_per_address():
    """
    Test vector-valued E: revenue per address.
    Should use: sum(E[i]*p[i] for i in R_reduced) - sum(E[i]*p[i] for i in R) - APR*C
    """
    print("\n=== CASE 6: Vector E per address ===")

    E = [2.0, 10.0, 5.0]   # Revenue differs per address
    APR = 0.5
    p = [3, 1, 2]
    R = [0, 1, 2]
    S = {1}
    C = -20.0
    C2 = compute_coverage_change(E, APR, p, R, S, C)
    print("C2 =", C2)

    expected = 0.0
    assert np.isclose(C2, expected)
    assert isinstance(C2, numbers.Real)

if __name__ == "__main__":
    test_case_1_remove_nothing()
    test_case_2_remove_one()
    test_case_3_remove_two()
    test_case_4_remove_all()
    test_case_5_remove_one_increases_coverage()
    test_case_6_vector_E_per_address()