from libraries.utils.algorithm.structural_heuristics.union_helpers import _build_union_candidates

def test_case_1_basic_unions():
    """
    Three singleton sets → all pairwise unions + full union.
    """
    S1 = frozenset({1})
    S2 = frozenset({2})
    S3 = frozenset({3})
    promising = [S1, S2, S3]
    unions = _build_union_candidates(promising)
    print("\nTest U1 — Basic unions (no limits):")
    for u in sorted(unions, key=lambda x: (len(x), sorted(x))):
        print(" ", u)
    expected = {
        frozenset({1, 2}),
        frozenset({1, 3}),
        frozenset({2, 3}),
        frozenset({1, 2, 3}),
    }
    assert unions == expected, f"Expected {expected}, got {unions}"


def test_case_2_max_combination_size():
    """
    max_combination_size=2 → only pairwise unions.
    """
    S1 = frozenset({1})
    S2 = frozenset({2})
    S3 = frozenset({3})
    promising = [S1, S2, S3]
    unions = _build_union_candidates(
        promising,
        max_combination_size=2,
    )
    print("\nTest U2 — max_combination_size=2:")
    for u in sorted(unions, key=lambda x: sorted(x)):
        print(" ", u)
    expected = {
        frozenset({1, 2}),
        frozenset({1, 3}),
        frozenset({2, 3}),
    }
    assert unions == expected, f"Expected {expected}, got {unions}"

def test_case_3_max_union_size():
    """
    max_union_size filters large unions.
    """
    S1 = frozenset({1, 2})
    S2 = frozenset({3})
    S3 = frozenset({4})
    promising = [S1, S2, S3]
    unions = _build_union_candidates(
        promising,
        max_union_size=3,
    )
    print("\nTest U3 — max_union_size=3:")
    for u in sorted(unions, key=lambda x: (len(x), sorted(x))):
        print(" ", u)
    expected = {
        frozenset({1, 2, 3}),
        frozenset({1, 2, 4}),
        frozenset({3, 4}),
    }
    assert unions == expected, f"Expected {expected}, got {unions}"


def test_case_4_both_limits():
    """
    Both max_combination_size and max_union_size active.
    """
    S1 = frozenset({1, 2})
    S2 = frozenset({3})
    S3 = frozenset({4})
    promising = [S1, S2, S3]
    unions = _build_union_candidates(
        promising,
        max_combination_size=2,
        max_union_size=3,
    )
    print("\nTest U4 — both limits applied:")
    for u in sorted(unions, key=lambda x: (len(x), sorted(x))):
        print(" ", u)
    expected = {
        frozenset({1, 2, 3}),
        frozenset({1, 2, 4}),
        frozenset({3, 4}),
    }
    assert unions == expected, f"Expected {expected}, got {unions}"

def test_case_5_both_limits():
    """
    Both max_combination_size and max_union_size active.
    """
    S1 = frozenset({1, 2})
    S2 = frozenset({3})
    S3 = frozenset({4})
    promising = [S1, S2, S3]
    unions = _build_union_candidates(
        promising,
        max_combination_size=2,
        max_union_size=3,
        min_union_size=3,
    )
    print("\nTest U4 — both limits applied:")
    for u in sorted(unions, key=lambda x: (len(x), sorted(x))):
        print(" ", u)
    expected = {
        frozenset({1, 2, 3}),
        frozenset({1, 2, 4}),
    }
    assert unions == expected, f"Expected {expected}, got {unions}"

def test_case_6_edge_cases():
    """
    Edge cases: fewer than two promising sets.
    """
    print("\nTest U5 — edge cases:")
    empty = _build_union_candidates([])
    single = _build_union_candidates([frozenset({1})])
    print(" empty input →", empty)
    print(" single input →", single)
    assert empty == set(), "Expected empty set for empty input"
    assert single == set(), "Expected empty set for single-element input"


if __name__ == "__main__":
    test_case_1_basic_unions()
    test_case_2_max_combination_size()
    test_case_3_max_union_size()
    test_case_4_both_limits()
    test_case_5_both_limits()
    test_case_6_edge_cases()
