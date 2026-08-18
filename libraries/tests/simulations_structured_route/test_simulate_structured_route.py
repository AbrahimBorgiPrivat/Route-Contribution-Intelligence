import numpy as np
from libraries.utils.experiments.simulations_structured_route import (
    simulate_structured_route,
)


def print_matrix(D):
    """Helper function to print matrices in a readable form."""
    with np.printoptions(precision=3, suppress=True):
        print(D)


def test_case_1_basic_structure():
    """
    Basic test: small number of units, no asymmetry, no outliers.
    Checks dimensions and node consistency.
    """
    print("\n=== TEST CASE 1: Basic structured simulation ===")

    n_units = 3
    seed = 42

    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=2,
        seed=seed,
        asymmetry_strength=0.0,
        outlier_fraction=0.0,
    )

    n_addresses = sum(1 for n in nodes if n["type"] == "address")
    n_total = n_addresses + 2 * n_units

    assert D_big.shape == (n_total, n_total)
    assert len(nodes) == n_total
    assert len(p) == n_addresses

    # Symmetric when no asymmetry is requested
    assert np.allclose(D_big, D_big.T)

    # Postboxes must be positive
    assert np.all(p >= 1)


def test_case_2_node_types_and_units():
    """
    Verify exactly one start and one end per unit,
    and at least one address per unit.
    """
    print("\n=== TEST CASE 2: Node type integrity ===")

    n_units = 5
    seed = 123

    _, nodes, _ = simulate_structured_route(
        n_units=n_units,
        min_unit_size=1,
        max_unit_size=4,
        seed=seed,
    )

    units = {}
    for n in nodes:
        units.setdefault(n["unit"], []).append(n)

    assert set(units.keys()) == set(range(n_units))

    for u, elems in units.items():
        starts = [n for n in elems if n["type"] == "start"]
        ends = [n for n in elems if n["type"] == "end"]
        addresses = [n for n in elems if n["type"] == "address"]

        assert len(starts) == 1, f"Unit {u} has {len(starts)} start nodes"
        assert len(ends) == 1, f"Unit {u} has {len(ends)} end nodes"
        assert len(addresses) >= 1, f"Unit {u} has no addresses"


def test_case_3_asymmetry():
    """
    Asymmetry test: with asymmetry_strength > 0,
    distance matrix should not be symmetric.
    """
    print("\n=== TEST CASE 3: Asymmetric structured simulation ===")

    n_units = 4
    seed = 321

    D_big, _, _ = simulate_structured_route(
        n_units=n_units,
        seed=seed,
        asymmetry_strength=0.5,
    )

    asym_fraction = np.mean(~np.isclose(D_big, D_big.T))
    assert asym_fraction > 0.1


def test_case_4_outer_outliers():
    """
    Outlier test: some units should be placed far away when outlier_fraction > 0.
    """
    print("\n=== TEST CASE 4: Outer outliers ===")

    n_units = 6
    seed = 999
    outlier_fraction = 0.33

    D_big, nodes, _ = simulate_structured_route(
        n_units=n_units,
        seed=seed,
        outlier_fraction=outlier_fraction,
        asymmetry_strength=0.2,
    )

    # Pick start node of unit 0
    start_node = next(
        n for n in nodes if n["unit"] == 0 and n["type"] == "start"
    )
    start_idx = start_node["m_index"]

    distances = D_big[start_idx]
    median_dist = np.median(D_big[D_big > 0])

    assert np.max(distances) > 2 * median_dist


def test_case_5_reproducibility():
    """
    Same seed must generate identical D_big, nodes, and p.
    """
    print("\n=== TEST CASE 5: Reproducibility ===")

    n_units = 5
    seed = 2024

    D1, nodes1, p1 = simulate_structured_route(
        n_units=n_units,
        seed=seed,
        asymmetry_strength=0.1,
    )
    D2, nodes2, p2 = simulate_structured_route(
        n_units=n_units,
        seed=seed,
        asymmetry_strength=0.1,
    )

    assert np.allclose(D1, D2)
    assert nodes1 == nodes2
    assert np.array_equal(p1, p2)


def test_case_6_route_number_consistency():
    """
    route_number values must be contiguous and match p indexing.
    """
    print("\n=== TEST CASE 6: route_number consistency ===")

    n_units = 4
    seed = 77

    _, nodes, p = simulate_structured_route(
        n_units=n_units,
        seed=seed,
    )

    route_numbers = sorted(
        n["route_number"]
        for n in nodes
        if n["type"] == "address"
    )

    assert route_numbers == list(range(len(p)))


if __name__ == "__main__":
    test_case_1_basic_structure()
    test_case_2_node_types_and_units()
    test_case_3_asymmetry()
    test_case_4_outer_outliers()
    test_case_5_reproducibility()
    test_case_6_route_number_consistency()
