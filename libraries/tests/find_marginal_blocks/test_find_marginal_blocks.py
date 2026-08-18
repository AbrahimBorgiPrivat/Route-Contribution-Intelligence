
import numpy as np
from libraries.utils.algorithm.structural_heuristics.find_marginal_blocks import find_marginal_blocks

def test_case_1():
    """
    Main example: 8-node matrix.
    The marginal blocks depend on p, E, APR.
    Checks:
      - blocks is a list
      - all elements are frozensets
      - no errors occur
    """
    D = np.array([
        [ 0,12, 2, 3, 2,11, 3,13],
        [12, 0,13,14,13, 2,12,12],
        [ 2,13, 0, 2, 3,12, 3,14],
        [ 3,14, 2, 0, 2,13, 2,13],
        [ 2,13, 3, 2, 0,14, 3,12],
        [11, 2,12,13,14, 0,12,12],
        [ 3,12, 3, 2, 3,12, 0,13],
        [13,12,14,13,12,12,13, 0],
    ])
    R = list(range(8))
    p = [1]*8
    E = 1.0
    APR = 0.1
    z = 0.0
    blocks = find_marginal_blocks(D=D, p=p, E=E, APR=APR, R=R, z=z, L_max=3)
    print("\nTest B1 — Marginal blocks:")
    for b in blocks:
        print(" ", b)
    assert isinstance(blocks, list)
    for S in blocks:
        assert isinstance(S, frozenset)

def test_case_2():
    """
    Block structure test:
    Margins arranged so two consecutive blocks exceed threshold.
    Checks:
      - blocks is not empty
      - each block is a frozenset
    """
    D = np.array([
        [0,1,10,20],
        [1,0,11,22],
        [10,11,0,1],
        [20,22,1,0]
    ])
    R = [0,1,2,3]
    p = [1,1,1,1]
    E = 1.0
    APR = 0.1
    z = -1.0
    blocks = find_marginal_blocks(D=D, p=p, E=E, APR=APR, R=R, z=z, L_max=3)
    print("\nTest B2 — Block marginal result:")
    for b in blocks:
        print(" ", b)
    assert isinstance(blocks, list)
    assert len(blocks) > 0     
    for S in blocks:
        assert isinstance(S, frozenset)

def test_case_3():
    """
    Case where marginal C2({i}) is always negative: no blocks.
    Checks: Blocks should be empty list
    """
    D = np.array([
        [0,1,2],
        [1,0,3],
        [2,3,0]
    ])
    R = [0,1,2]
    p = [1,1,1]
    E = 5.0 
    APR = 0.5
    z = 0
    blocks = find_marginal_blocks(D=D, p=p, E=E, APR=APR, R=R, z=z, L_max=2)
    print("\nTest B3 — No marginal blocks expected:")
    print(" ", blocks)
    assert isinstance(blocks, list)
    assert len(blocks) == 0

def test_case_4():
    """
    Test vector-valued E: ΔDG(i) uses E[i] * p[i].
    """
    D = np.array([
        [0,  5,  6],
        [5,  0,100],
        [6,100,  0],
    ])
    R = [0, 1, 2]
    p = [1, 1, 1]
    E = [1.0, 20.0, 1.0]     
    APR = 0.1
    z = -1.0
    blocks = find_marginal_blocks(D=D, p=p, E=E, APR=APR, R=R, z=z, L_max=3)
    print("\n=== Test B4 — Vector-valued E per address ===")
    print("Blocks:", blocks)
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    for S in blocks:
        assert isinstance(S, frozenset)
    assert any(1 not in S for S in blocks)

def test_case_5_scalar_Lu():
    """
    Test scalar inner length L_u:
    Removing nodes should include APR * L_u contribution.
    """
    D = np.array([
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ])
    R = [0, 1, 2]
    p = [1, 1, 1]
    E = 1.0
    APR = 1.0
    L_u = 10.0  
    z = 0.0
    blocks = find_marginal_blocks(
        D=D,
        p=p,
        E=E,
        APR=APR,
        R=R,
        z=z,
        L_u=L_u,
        L_max=2,
    )
    print("\nTest B5 — Scalar L_u blocks:")
    print(" ", blocks)
    assert isinstance(blocks, list)
    for S in blocks:
        assert isinstance(S, frozenset)
    assert len(blocks) > 0

def test_case_6_vector_Lu():
    """
    Test vector-valued L_u: different inner lengths per node.
    Nodes with large L_u should be more likely to appear in blocks.
    """
    D = np.array([
        [0, 2, 2],
        [2, 0, 2],
        [2, 2, 0],
    ])
    R = [0, 1, 2]
    p = [1, 1, 1]
    E = 1.0
    APR = 1.0
    L_u = [0.0, 10.0, 0.0]  
    z = 0.0

    blocks = find_marginal_blocks(
        D=D,
        p=p,
        E=E,
        APR=APR,
        R=R,
        z=z,
        L_u=L_u,
        L_max=2,
    )

    print("\nTest B6 — Vector L_u blocks:")
    print(" ", blocks)
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert any(1 in S for S in blocks)

def test_case_7_invalid_Lu_length():
    """
    Error test: L_u vector length does not match p/R.
    Should raise ValueError.
    """
    import pytest
    D = np.array([
        [0, 1],
        [1, 0],
    ])
    R = [0, 1]
    p = [1, 1]
    E = 1.0
    APR = 0.1
    L_u = [1.0] 
    z = 0.0
    print("\nTest B7 — L_u vector length does not match")
    with pytest.raises(ValueError, match="Length of L_u must match"):
        find_marginal_blocks(
            D=D,
            p=p,
            E=E,
            APR=APR,
            R=R,
            z=z,
            L_u=L_u,
        )

if __name__ == "__main__":
    test_case_1()
    test_case_2()
    test_case_3()
    test_case_4()
    test_case_5_scalar_Lu()
    test_case_6_vector_Lu()
    test_case_7_invalid_Lu_length()