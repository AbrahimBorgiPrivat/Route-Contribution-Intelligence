import numpy as np
import pytest

from libraries.utils.algorithm.solvers.common import inner_length

def test_case_A_scalar_Lu():
    print("\n=== CASE A: Scalar L_u ===")
    R = [0, 1, 2, 3]
    route = [2, 0, 3]
    L_u = 1.5
    L = inner_length(R, route, L_u)
    print("Inner length:", L)
    assert np.isclose(L, 1.5 * len(route))

def test_case_B_vector_Lu_full_route():
    print("\n=== CASE B: Vector L_u (full route) ===")
    R = [0, 1, 2]
    route = [0, 1, 2]
    L_u = [1.0, 2.0, 3.0]
    L = inner_length(R, route, L_u)
    print("Inner length:", L)
    assert np.isclose(L, 1.0 + 2.0 + 3.0)

def test_case_C_vector_Lu_reduced_route():
    print("\n=== CASE C: Vector L_u (reduced route) ===")

    R = [0, 1, 2, 3]
    route = [2, 0, 3]
    L_u = [10.0, 20.0, 30.0, 40.0]
    L = inner_length(R, route, L_u)
    print("Inner length:", L)
    assert np.isclose(L, 30.0 + 10.0 + 40.0)

def test_case_D_empty_route():
    print("\n=== CASE D: Empty route ===")
    R = [0, 1, 2]
    route = []
    L_u = [1.0, 2.0, 3.0]
    L = inner_length(R, route, L_u)
    print("Inner length:", L)
    assert np.isclose(L, 0.0)

# ---------------------------------------------------------
# Manual execution
# ---------------------------------------------------------
if __name__ == "__main__":
    test_case_A_scalar_Lu()
    test_case_B_vector_Lu_full_route()
    test_case_C_vector_Lu_reduced_route()
    test_case_D_empty_route()
