from libraries.utils.algorithm.single_route.outlier_detection import detect_outliers

def test_case_1_basic_single_outlier():
    """
    Simple structure:
        S={1} positive (C2>z)
        S_sup={1,2} negative (C2<z)
    => {1} should be detected.
    """
    print("\n=== CASE 1: Basic single outlier ===")
    C2 = {
        frozenset({1}):  5.0,     # > z
        frozenset({2}): -1.0,
        frozenset({1,2}): -10.0,  # < z
    }
    z = 0.0
    S_sig, cov = detect_outliers(C2, z)
    print("Outliers:", S_sig)
    assert frozenset({1}) in S_sig
    assert frozenset({1}) in cov
    assert len(S_sig) == 1

def test_case_2_no_outliers():
    """
    No set satisfies the condition C2(S)>z AND exists S'>S with C2(S')<z.
    """
    print("\n=== CASE 2: No outliers ===")
    C2 = {
        frozenset({1}): -1.0,    # <= z
        frozenset({2}): -2.0,    # <= z
        frozenset({1,2}): -3.0,  # <= z
    }
    z = 0.0
    S_sig, cov = detect_outliers(C2, z)
    print("Outliers:", S_sig)
    assert len(S_sig) == 0
    assert len(cov) == 0

def test_case_3_multi_level():
    """
    Multi-level outlier detection:
        {1}, {2} qualify as positive,
        {1,2} is negative -> both should be outliers.
    """
    print("\n=== CASE 3: Multi-level ===")
    C2 = {
        frozenset({1}): 4.0,
        frozenset({2}): 2.0,
        frozenset({3}): -1.0,
        frozenset({1,2}): -5.0,
        frozenset({2,3}): -2.0,
    }
    z = 0.0
    S_sig, _ = detect_outliers(C2, z)
    print("Outliers:", S_sig)
    assert frozenset({1}) in S_sig
    assert frozenset({2}) in S_sig
    assert frozenset({3}) not in S_sig
    assert len(S_sig) == 2

def test_case_4_superset_is_positive():
    """
    Important edge:
      If S has C2(S)>0,
      but all supersets also have C2>=0,
      then S is NOT an outlier.
    """
    print("\n=== CASE 4: Superset positive -> no outlier ===")
    C2 = {
        frozenset({1}):  5.0,
        frozenset({2}):  1.0,
        frozenset({1,2}): 3.0,   # POSITIVE
    }
    z = 0.0
    S_sig, cov = detect_outliers(C2, z)
    print("Outliers:", S_sig)
    assert len(S_sig) == 0
    assert len(cov) == 0

def test_case_5_threshold_effect():
    """
    Using z != 0:
    Only sets with C2(S) > z qualify,
    but still must have a negative superset.
    """
    print("\n=== CASE 5: Threshold effect z=2 ===")
    C2 = {
        frozenset({1}): 3.0,    # > 2, candidate
        frozenset({2}): 5.0,    # > 2
        frozenset({1,2}): -1.0, # < z
    }
    z = 2.0
    S_sig, _ = detect_outliers(C2, z)
    print("Outliers:", S_sig)
    assert frozenset({1}) in S_sig
    assert frozenset({2}) in S_sig

if __name__ == "__main__":
    test_case_1_basic_single_outlier()
    test_case_2_no_outliers()
    test_case_3_multi_level()
    test_case_4_superset_is_positive()
    test_case_5_threshold_effect()
