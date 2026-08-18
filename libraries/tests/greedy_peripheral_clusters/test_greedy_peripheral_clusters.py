import numpy as np
from libraries.utils.algorithm.structural_heuristics.greedy_peripheral_clusters import greedy_peripheral_clusters

def test_case_1():
    """
    Main example: Nodes 1,5,7 are a clear peripheral cluster.
    We expect:
      - clusters is a list
      - clusters contain frozensets
      - one cluster should contain subset of {1,5,7}
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
    clusters = greedy_peripheral_clusters(
        D=D,
        R=R,              
        method="kneedle",
        combine_clusters=False
    )
    print("\nTest A1 — Peripheral clusters:")
    for c in clusters:
        print(" ", c)
    assert isinstance(clusters, list)
    for c in clusters:
        assert isinstance(c, frozenset)
    target = {1,5,7}
    found = any(len(c & target) >= 2 for c in clusters)
    assert found, "Expected cluster containing a subset of {1,5,7}"

def test_case_2():
    """
    Easy 2-cluster test:
    Cluster 1: {0,1,2}
    Cluster 2: {3,4,5}
    Distances between clusters are large.
    """
    D = np.array([
        [0,1,2,20,20,21],
        [1,0,1,19,20,22],
        [2,1,0,18,22,23],
        [20,19,18,0,1,1],
        [20,20,22,1,0,2],
        [21,22,23,1,2,0],
    ])
    R = list(range(6))
    clusters = greedy_peripheral_clusters(
        D=D,
        R=R,
        method="kneedle"
    )
    print("\nTest A2 — Expected two obvious clusters:")
    for c in clusters:
        print(" ", c)
    assert isinstance(clusters, list)
    for c in clusters:
        assert isinstance(c, frozenset)
    big_clusters = [c for c in clusters if len(c) >= 2]
    assert len(big_clusters) == 2, f"Expected 2 main clusters, got {big_clusters}"

def test_case_3():
    """
    Uniform grid test: no true periphery.
    All distances are similar → should return only one cluster.
    """
    D = np.array([
        [0,3,4,5],
        [3,0,4,5],
        [4,4,0,4],
        [5,5,4,0],
    ])
    R = list(range(4))
    clusters = greedy_peripheral_clusters(
        D=D,
        R=R,
        method="kneedle"
    )
    print("\nTest A3 — Uniform grid (1 cluster expected):")
    for c in clusters:
        print(" ", c)
    assert isinstance(clusters, list)
    for c in clusters:
        assert isinstance(c, frozenset)
    assert len(clusters) == 0, f"Expected 1 cluster, but got {clusters}"

if __name__ == "__main__":
    test_case_1()
    test_case_2()
    test_case_3()