import numbers
import numpy as np
from typing import Optional, Dict, Any, List

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.core_algorithm import find_outliers
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data

def run_test(
    strict_order: bool,
    label: str,
    n: int = 10,
    E: float | Optional[Dict[str, Any]] = None,
    APR: float = 0.05,
    solvers: Optional[List[str]] = None,
    *,
    L_u: float | List[float] | None = None,
    problem_type: str = "TSP",
):
    print("\n====================================================")
    print(f"TEST: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  E-type={type(E).__name__}")
    print("====================================================")

    # ----------------------------------------------------
    # Default solvers
    # ----------------------------------------------------
    if solvers is None:
        solvers = ["lkh", "python_tsp", "ortools", "greedy"]

    # ----------------------------------------------------
    # SIMULATE INPUT DATA
    # ----------------------------------------------------
    outlier_fraction = 0.1
    asymmetry_strength = 0.10
    seed = 2719

    if E is None:
        D, p = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
        )
        E_used = 5.0
    elif isinstance(E, (float, int, np.floating, np.integer)):
        D, p = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
        )
        E_used = E
    else:
        out = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
            E=E,
        )
        D, p, E_vec = out
        E_used = E_vec

    z = 0.0

    # ----------------------------------------------------
    # RUN FIND_OUTLIERS FOR EACH SOLVER
    # ----------------------------------------------------
    for solver in solvers:
        print("\n----------------------------------------------------")
        print(f"Running find_outliers with solver='{solver}'")
        print("----------------------------------------------------")

        (
            coverage_change,
            C_distance_outliers,
            R_original,
            R_star,
            L_original,
            L_opt,
            S_outlier,
            C2_max,
            DG_original,
            DG_best,
        ) = find_outliers(
            D=D,
            p=p,
            E=E_used,
            APR=APR,
            strict_order=strict_order,
            z=z,
            solver=solver,
            deterministic=True,
            ortools_time_limit=3,
            L_u=L_u if L_u is not None else 0.0,
            problem_type=problem_type,
        )

        # ------------------------------------------------
        # OUTPUT
        # ------------------------------------------------
        print("\n--- SIGNIFICANT OUTLIER SUBSETS ---")
        for S, val in coverage_change.items():
            print(f"  S={set(S)},  C2={val:.4f},  Dist.Change={C_distance_outliers[S]}")

        print("\n--- ROUTES ---")
        print(f"Original route:        {R_original}")
        print(f"Outlier-cleaned route: {R_star}")

        print("\n--- LENGTHS ---")
        print(f"L(R_original) = {L_original:.4f}")
        print(f"L(R_star)     = {L_opt:.4f}")

        print("\n--- BEST OUTLIER SUBSET ---")
        print(f"S_outlier = {set(S_outlier)}")
        print(f"C2_max    = {C2_max:.4f}")

        print("\n--- ECONOMIC SUMMARY ---")
        print(f"DG(original) = {DG_original:.4f}")
        print(f"DG(best)     = {DG_best:.4f}")

        # ------------------------------------------------
        # VALIDATION
        # ------------------------------------------------
        assert isinstance(coverage_change, dict)
        assert isinstance(R_original, list)
        assert isinstance(R_star, list)

        assert isinstance(L_original, numbers.Real)
        assert isinstance(L_opt, numbers.Real)
        assert isinstance(C2_max, numbers.Real)
        assert isinstance(DG_original, numbers.Real)
        assert isinstance(DG_best, numbers.Real)

        assert L_original > 0
        assert L_opt >= 0
        assert DG_best >= DG_original

        for S, v in coverage_change.items():
            assert isinstance(S, frozenset)
            assert isinstance(v, numbers.Real)

        for s in S_outlier:
            assert s not in R_star

        assert all(0 <= x < n for x in R_original)
        assert all(0 <= x < n for x in R_star)

        if set(R_original) != set(R_star):
            assert len(S_outlier) > 0


def run_test_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n_units: int = 4,
    solver: str = "ortools",
    E: float | Optional[Dict[str, Any]] = 5.0,
    APR=0.5,
):
    print("\n====================================================")
    print(f"TEST (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")

    # --------------------------------------------------
    # Simulate structured instance
    # --------------------------------------------------
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2024,
        asymmetry_strength=0.1,
    )

    if isinstance(E, list):
        if len(E) == 1:
            E = E * len(p)
        elif len(E) != len(p):
            raise ValueError(
                f"Structured test: len(E)={len(E)} must match len(p)={len(p)}"
            )

    (
        coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_outlier,
        C2_max,
        DG_original,
        DG_best,
    ) = find_outliers(
        D=D_big,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        z=0.0,
        solver=solver,
        deterministic=True,
        ortools_time_limit=3,
        problem_type=problem_type,
        nodes=nodes,
    )
    print("\n--- SIGNIFICANT OUTLIER SUBSETS ---")
    for S, val in coverage_change.items():
        print(f"  S={set(S)},  C2={val:.4f},  Dist.Change={C_distance_outliers[S]}")

    print("\n--- ROUTES ---")
    print(f"Original route:        {R_original}")
    print(f"Outlier-cleaned route: {R_star}")

    print("\n--- LENGTHS ---")
    print(f"L(R_original) = {L_original:.4f}")
    print(f"L(R_star)     = {L_opt:.4f}")

    print("\n--- BEST OUTLIER SUBSET ---")
    print(f"S_outlier = {set(S_outlier)}")
    print(f"C2_max    = {C2_max:.4f}")

    print("\n--- ECONOMIC SUMMARY ---")
    print(f"DG(original) = {DG_original:.4f}")
    print(f"DG(best)     = {DG_best:.4f}")

    assert isinstance(coverage_change, dict)
    assert isinstance(R_original, list)
    assert isinstance(R_star, list)
    assert isinstance(L_original, numbers.Real)
    assert isinstance(L_opt, numbers.Real)
    assert isinstance(C2_max, numbers.Real)
    assert isinstance(DG_original, numbers.Real)
    assert isinstance(DG_best, numbers.Real)
    assert L_original >= 0
    assert L_opt >= 0
    assert DG_best >= DG_original
    for S in coverage_change:
        assert isinstance(S, frozenset)
    for s in S_outlier:
        assert s not in R_star

def run_test_return_c_distance(
    strict_order: bool,
    label: str,
    n: int = 10,
    E: float = 5.0,
    APR: float = 0.05,
    problem_type: str = "TSP",
    ):
    print("\n====================================================")
    print(f"TEST (return_c_distance=True): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print("====================================================")
    D, p = simulate_addresses(
        n=n,
        seed=2719,
        asymmetry_strength=0.10,
        outlier_fraction=0.1,
    )
    z = 0.0
    (
        result,
        C_distance_all,
    ) = find_outliers(
        D=D,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        z=z,
        solver="greedy",
        deterministic=True,
        ortools_time_limit=3,
        L_u=0.0,
        problem_type=problem_type,
        return_c_distance=True,
    )
    (
        coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_outlier,
        C2_max,
        DG_original,
        DG_best,
    ) = result
    assert isinstance(C_distance_all, dict)
    assert isinstance(C_distance_outliers, dict)
    assert isinstance(C_distance_all, dict)
    assert isinstance(C_distance_outliers, dict)
    expected_keys = {
        "C_distance_full",
        "D_outer",
        "D_all",
        "inner_models",
        "inner_solver",
        "inner_cache",
        "outer_cache",
    }

    assert expected_keys.issubset(set(C_distance_all.keys()))
    assert isinstance(C_distance_all["C_distance_full"], dict)
    assert C_distance_all["D_outer"] is None
    assert C_distance_all["D_all"] is None
    assert C_distance_all["inner_models"] is None
    assert C_distance_all["inner_solver"] is None
    assert C_distance_all["inner_cache"] is None
    assert C_distance_all["outer_cache"] is None
    assert len(C_distance_all["C_distance_full"]) >= len(C_distance_outliers)
    for S, v in C_distance_all["C_distance_full"].items():
        assert isinstance(S, frozenset)
        assert isinstance(v, numbers.Real)
    for S in C_distance_outliers:
        assert S in C_distance_all["C_distance_full"]
    assert DG_best >= DG_original
    assert set(R_star) == set(R_original) - set(S_outlier)

def run_test_structured_return_c_distance(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    n_units: int = 4,
    solver: str = "greedy",
    E: float = 5.0,
    APR: float = 0.5,
    ):
    print("\n====================================================")
    print(f"TEST (STRUCTURED, return_c_distance=True): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  solver={solver}")
    print("====================================================")
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2024,
        asymmetry_strength=0.1,
    )
    (
        result,
        C_distance_all,
    ) = find_outliers(
        D=D_big,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        z=0.0,
        solver=solver,
        deterministic=True,
        ortools_time_limit=3,
        problem_type=problem_type,
        nodes=nodes,
        return_c_distance=True,
    )
    (
        coverage_change,
        C_distance_outliers,
        R_original,
        R_star,
        L_original,
        L_opt,
        S_outlier,
        C2_max,
        DG_original,
        DG_best,
    ) = result
    assert isinstance(C_distance_all, dict)
    assert isinstance(C_distance_all, dict)
    assert isinstance(C_distance_outliers, dict)
    expected_keys = {
        "C_distance_full",
        "D_outer",
        "D_all",
        "inner_models",
        "inner_solver",
        "inner_cache",
        "outer_cache",
    }
    assert expected_keys.issubset(set(C_distance_all.keys()))
    assert isinstance(C_distance_all["C_distance_full"], dict)
    assert C_distance_all["D_outer"] is not None
    assert C_distance_all["D_all"] is not None
    assert C_distance_all["inner_models"] is not None
    assert C_distance_all["inner_solver"] is not None
    assert (
        C_distance_all["inner_cache"] is None
        or isinstance(C_distance_all["inner_cache"], dict)
    )
    assert (
        C_distance_all["outer_cache"] is None
        or isinstance(C_distance_all["outer_cache"], dict)
    )
    assert len(C_distance_all["C_distance_full"]) >= len(C_distance_outliers)
    for S, v in C_distance_all["C_distance_full"].items():
        assert isinstance(S, frozenset)
        assert isinstance(v, numbers.Real)
    assert DG_best >= DG_original
    assert set(R_star) == set(R_original) - set(S_outlier)


def test_find_outliers():
    run_test(
        strict_order=True,
        label="EXAMPLE 1: strict_order=True",
        E=5.0,
    )
    run_test(
        strict_order=False,
        label="EXAMPLE 2: strict_order=False",
        E=5.0,
    )
    E_dict = {"val": 5.0, "deviation": 2.0, "seed": 999}
    run_test(
        strict_order=True,
        label="EXAMPLE 3: strict_order=True, vector E",
        E=E_dict,
    )
    run_test(
        strict_order=False,
        label="EXAMPLE 4: strict_order=False, vector E",
        E=E_dict,
    )
    run_test(
        strict_order=True,
        label="EXAMPLE 5: strict_order=True, E<0",
        E=-100,
    )
    run_test(
        strict_order=True,
        label="EXAMPLE 6: strict_order=True, APR<0",
        APR=-100,
    )
    run_test(
        strict_order=False,
        label="EXAMPLE 7: HPP + greedy + scalar L_u",
        E=5.0,
        L_u=2.5,
        problem_type="HPP",
        solvers=["greedy"],
    )
    n = 10
    rng = np.random.default_rng(42)
    L_u_vec = rng.uniform(0.5, 3.0, size=n)
    run_test(
        strict_order=False,
        label="EXAMPLE 8: HPP + greedy dnn + vector L_u",
        n=n,
        E=5.0,
        L_u=L_u_vec,
        problem_type="HPP",
        solvers=["greedy_denn",],
    )
    run_test(
        strict_order=False,
        label="EXAMPLE 9: HPP + cheapest_insertion",
        E=5.0,
        problem_type="HPP",
        solvers=["cheapest_insertion"],
    )
    run_test_return_c_distance(
        strict_order=False,
        label="Exact — return_c_distance=True — unstructured",
    )

def test_find_outliers_structured():
    run_test_structured(
        label="OUT:HPP — Type 1 — scalar E",
        strict_order=True,
        problem_type="OUT:HPP",
        solver="ortools",
        E=5.0,
    )
    run_test_structured(
        label="OUT:HPP — Type 2 — greedy — scalar E",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        E=5.0,
    )
    run_test_structured(
        label="OUT:HPP — Type 2 — vector E (list)",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        E=[5.0],   
    )
    run_test_structured(
        label="OUT:TSP — Type 1 — scalar E",
        strict_order=True,
        problem_type="OUT:TSP",
        solver="ortools",
        E=5.0,
    )
    run_test_structured(
        label="OUT:TSP — Type 2 — greedy — scalar E",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="greedy",
        E=5.0,
    )
    run_test_structured(
        label="OUT:TSP — Type 2 — vector E (list)",
        strict_order=False,
        problem_type="OUT:TSP",
        solver="greedy",
        E=[5.0],
    )
    run_test_structured(
        label="OUT:HPP — Type 2 — APR < 0",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        E=5.0,
        APR=-0.2,
    )
    run_test_structured_return_c_distance(
        label="OUT:HPP — return_c_distance=True",
        strict_order=False,
        problem_type="OUT:HPP",
        solver="greedy",
        E=5.0,
    )


if __name__ == "__main__":
    test_find_outliers()
    test_find_outliers_structured()