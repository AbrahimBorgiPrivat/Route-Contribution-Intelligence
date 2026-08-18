import numbers
import numpy as np
from typing import Dict, Any, Optional, List

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.algorithm.single_route.core_algorithm import find_outliers_hybrid
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data

def run_test_hybrid(
    strict_order: bool,
    label: str,
    n: int = 10,
    E: float | Optional[Dict[str, Any]] = None,
    APR: float = 0.05,
    methods=None,
    solvers: Optional[List[str]] = None,
    A_kwargs=None,
    B_kwargs=None,
    *,
    L_u: float | List[float] | None = None,
    problem_type: str = "TSP",
):
    print("\n====================================================")
    print(f"TEST HYBRID: {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  E-type={type(E).__name__}")
    print("====================================================")

    # ----------------------------------------------------
    # Defaults
    # ----------------------------------------------------
    if methods is None:
        methods = ["A", "B", "Beam"]
    if A_kwargs is None:
        A_kwargs = {"method": "kneedle"}
    if B_kwargs is None:
        B_kwargs = {"L_max": 6}
    if solvers is None:
        solvers = ["lkh", "python_tsp", "ortools", "greedy"]

    # ----------------------------------------------------
    # SIMULATE INPUT DATA
    # ----------------------------------------------------
    outlier_fraction = 0.1
    asymmetry_strength = 0.10
    cluster_strength=0.5
    seed = 2719

    if E is None:
        D, p = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            cluster_strength=cluster_strength,
            outlier_fraction=outlier_fraction,
        )
        E_used = 5.0
    elif isinstance(E, (float, int, np.floating, np.integer)):
        D, p = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            cluster_strength=cluster_strength,
            outlier_fraction=outlier_fraction,
        )
        E_used = E
    else:
        # Vector-valued E
        out = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            cluster_strength=cluster_strength,
            outlier_fraction=outlier_fraction,
            E=E,
        )
        D, p, E_vec = out
        E_used = E_vec

    z = 0.0
    k_all = 1
    k_max = 5
    B = 10
    precheck = True

    # ----------------------------------------------------
    # RUN HYBRID OUTLIER DETECTION FOR EACH SOLVER
    # ----------------------------------------------------
    for solver in solvers:
        print("\n----------------------------------------------------")
        print(f"Running Hybrid Outlier Detection with solver='{solver}'")
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
        ) = find_outliers_hybrid(
            D=D,
            p=p,
            E=E_used,
            APR=APR,
            strict_order=strict_order,
            z=z,
            k_all=k_all,
            k_max=k_max,
            B=B,
            precheck=precheck,
            methods=methods,
            A_kwargs=A_kwargs,
            B_kwargs=B_kwargs,
            deterministic=True,
            solver=solver,
            ortools_time_limit=3,
            L_u=L_u if L_u is not None else 0.0,
            problem_type=problem_type,
        )

        # ------------------------------------------------
        # PRINT RESULTS
        # ------------------------------------------------
        print("\n--- SIGNIFICANT OUTLIER SUBSETS ---")
        for S, val in coverage_change.items():
            print(f"  S={set(S)},  C2={val:.4f},  DistChange={C_distance_outliers[S]}")

        print("\n--- ROUTES ---")
        print(f"Original route: {R_original}")
        print(f"Hybrid route:   {R_star}")

        print("\n--- ROUTE LENGTHS ---")
        print(f"L(R_original) = {L_original:.4f}")
        print(f"L(R_star)     = {L_opt:.4f}")

        print("\n--- BEST OUTLIER SUBSET ---")
        print(f"S_outlier = {set(S_outlier)}")
        print(f"C2_max    = {C2_max:.4f}")

        print("\n--- ECONOMIC SUMMARY ---")
        print(f"DG(original) = {DG_original:.4f}")
        print(f"DG(best)     = {DG_best:.4f}")

        # ------------------------------------------------
        # VALIDATION (robust invariants)
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

        assert set(R_star) == set(R_original) - set(S_outlier)
        assert len(R_star) == len(R_original) - len(S_outlier)
        assert all(0 <= x < n for x in R_original)
        assert all(0 <= x < n for x in R_star)

def run_test_hybrid_structured(
    strict_order: bool,
    label: str,
    *,
    n_units: int = 4,
    E: float | List[float] | np.ndarray = 5.0,
    APR: float = 0.75,
    methods=None,
    solvers: Optional[List[str]] = None,
    A_kwargs=None,
    B_kwargs=None,
    problem_type: str = "OUT:HPP",
):
    print("\n====================================================")
    print(f"TEST HYBRID (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  E-type={type(E).__name__}")
    print("====================================================")

    # ----------------------------------------------------
    # Defaults
    # ----------------------------------------------------
    if methods is None:
        methods = ["A", "B", "Beam"]
    if A_kwargs is None:
        A_kwargs = {"method": "kneedle"}
    if B_kwargs is None:
        B_kwargs = {"L_max": 6}
    if solvers is None:
        solvers = ["ortools", "greedy"]

    # ----------------------------------------------------
    # SIMULATE STRUCTURED INPUT DATA
    # ----------------------------------------------------
    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2719,
        asymmetry_strength=0.1,
        cluster_strength=0.5,
    )

    # Build once to know R and address count
    _, inner_models, _ = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    n = len(R)

    # Ensure vector E length matches number of addresses
    if isinstance(E, list) and len(E) == 1:
        E_used = E * n
    else:
        E_used = E

    z = 0.0
    k_all = 1
    k_max = 5
    B = 10
    precheck = True

    # ----------------------------------------------------
    # RUN HYBRID OUTLIER DETECTION FOR EACH SOLVER
    # ----------------------------------------------------
    for solver in solvers:
        print("\n----------------------------------------------------")
        print(f"Running Structured Hybrid with solver='{solver}'")
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
        ) = find_outliers_hybrid(
            D=D_big,
            p=p,
            E=E_used,
            APR=APR,
            strict_order=strict_order,
            z=z,
            k_all=k_all,
            k_max=k_max,
            B=B,
            precheck=precheck,
            methods=methods,
            A_kwargs=A_kwargs,
            B_kwargs=B_kwargs,
            deterministic=True,
            solver=solver,
            ortools_time_limit=3,
            L_u=0.0,
            problem_type=problem_type,
            nodes=nodes,
        )

        # ------------------------------------------------
        # PRINT RESULTS
        # ------------------------------------------------
        print("\n--- SIGNIFICANT OUTLIER SUBSETS ---")
        for S, val in coverage_change.items():
            print(f"  S={set(S)},  C2={val:.4f},  DistChange={C_distance_outliers[S]}")

        print("\n--- ROUTES ---")
        print(f"Original route: {R_original}")
        print(f"Hybrid route:   {R_star}")

        print("\n--- ROUTE LENGTHS ---")
        print(f"L(R_original) = {L_original:.4f}")
        print(f"L(R_star)     = {L_opt:.4f}")

        print("\n--- BEST OUTLIER SUBSET ---")
        print(f"S_outlier = {set(S_outlier)}")
        print(f"C2_max    = {C2_max:.4f}")

        print("\n--- ECONOMIC SUMMARY ---")
        print(f"DG(original) = {DG_original:.4f}")
        print(f"DG(best)     = {DG_best:.4f}")


        # ------------------------------------------------
        # VALIDATION (structured invariants)
        # ------------------------------------------------
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
        for S, v in coverage_change.items():
            assert isinstance(S, frozenset)
            assert isinstance(v, numbers.Real)
        assert set(R_star) == set(R_original) - set(S_outlier)
        assert len(R_star) == len(R_original) - len(S_outlier)
        assert all(isinstance(x, int) for x in R_star)

def run_test_hybrid_return_c_distance(
    strict_order: bool,
    label: str,
    n: int = 10,
    E: float = 5.0,
    APR: float = 0.05,
    problem_type: str = "TSP",
):
    print("\n====================================================")
    print(f"TEST HYBRID (return_c_distance=True): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print("====================================================")

    D, p = simulate_addresses(
        n=n,
        seed=2719,
        asymmetry_strength=0.1,
        cluster_strength=0.5,
        outlier_fraction=0.1,
    )

    z = 0.0

    (
        result,
        C_distance_all,
    ) = find_outliers_hybrid(
        D=D,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        z=z,
        k_all=1,
        k_max=5,
        B=10,
        precheck=True,
        deterministic=True,
        solver="greedy",
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

    # ------------------------------------------------
    # VALIDATION (return_c_distance invariants)
    # ------------------------------------------------
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

    # Full structural dictionaries
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

def run_test_hybrid_structured_return_c_distance(
    strict_order: bool,
    label: str,
    *,
    n_units: int = 4,
    E: float = 5.0,
    APR: float = 0.75,
    problem_type: str = "OUT:HPP",
):
    print("\n====================================================")
    print(f"TEST HYBRID STRUCTURED (return_c_distance=True): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print("====================================================")

    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2719,
        asymmetry_strength=0.1,
        cluster_strength=0.5,
    )

    z = 0.0

    (
        result,
        C_distance_all,
    ) = find_outliers_hybrid(
        D=D_big,
        p=p,
        E=E,
        APR=APR,
        strict_order=strict_order,
        z=z,
        k_all=1,
        k_max=5,
        B=10,
        precheck=True,
        deterministic=True,
        solver="greedy",
        ortools_time_limit=3,
        L_u=0.0,
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

    # ------------------------------------------------
    # VALIDATION (structured return_c_distance)
    # ------------------------------------------------
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

    for S in C_distance_outliers:
        assert S in C_distance_all["C_distance_full"]

    assert DG_best >= DG_original
    assert set(R_star) == set(R_original) - set(S_outlier)

# =========================================================
# TEST SUITE
# =========================================================

def test_find_outliers_hybrid():
    run_test_hybrid(
        strict_order=True,
        label="Hybrid — strict_order=True, scalar E",
        E=5.0,
    )
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — strict_order=False, scalar E",
        E=5.0,
    )
    E_dict = {"val": 5.0, "deviation": 2.0, "seed": 999}
    run_test_hybrid(
        strict_order=True,
        label="Hybrid — strict_order=True, vector E",
        E=E_dict,
    )
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — strict_order=False, vector E",
        E=E_dict,
    )
    run_test_hybrid(
        strict_order=True,
        label="Hybrid — strict_order=True, E<0",
        E=-50,
    )
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — strict_order=False, APR<0",
        E=5.0,
        APR=-1.0,
    )
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — HPP + greedy + scalar L_u",
        E=5.0,
        L_u=2.0,
        problem_type="HPP",
        solvers=["greedy"],
    )
    n = 10
    rng = np.random.default_rng(42)
    L_u_vec = rng.uniform(0.5, 3.0, size=n)
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — HPP + greedy_denn + vector L_u",
        n=n,
        E=5.0,
        L_u=L_u_vec,
        problem_type="HPP",
        solvers=["greedy_denn"],
    )
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — HPP + cheapest_insertion",
        E=5.0,
        problem_type="HPP",
        solvers=["cheapest_insertion"],
    )

    run_test_hybrid(
        strict_order=True,
        label="Hybrid — HPP — U only",
        problem_type="HPP",
        methods=["U"],
    )
    
    run_test_hybrid(
        strict_order=False,
        label="Hybrid — OUT:TSP — A + B + Beam + U",
        problem_type="TSP",
        methods=["A", "B", "U"],
        solvers=["greedy"],
    )

    run_test_hybrid_return_c_distance(
        strict_order=False,
        label="Hybrid — return_c_distance=True — unstructured",
    )

def test_find_outliers_hybrid_structured():
    run_test_hybrid_structured(
        strict_order=True,
        label="Structured Hybrid — OUT:HPP — strict_order=True",
        problem_type="OUT:HPP",
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:HPP — strict_order=False",
        problem_type="OUT:HPP",
        solvers=["greedy"],
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:TSP — greedy",
        problem_type="OUT:TSP",
        solvers=["greedy"],
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:HPP — vector E",
        problem_type="OUT:HPP",
        E=[5.0], 
    )
    
    run_test_hybrid_structured(
        strict_order=True,
        label="Structured Hybrid — OUT:HPP — U only",
        problem_type="OUT:HPP",
        methods=["U"],
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:HPP — Beam + U",
        problem_type="OUT:HPP",
        methods=["Beam", "U"],
        solvers=["greedy"],
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:TSP — A + B + U",
        problem_type="OUT:TSP",
        methods=["A", "B", "U"],
        solvers=["greedy"],
    )

    run_test_hybrid_structured(
        strict_order=False,
        label="Structured Hybrid — OUT:TSP — A + B + Beam + U",
        problem_type="OUT:TSP",
        methods=["A", "B", "Beam", "U"],
        solvers=["greedy"],
    )

    run_test_hybrid_structured_return_c_distance(
        strict_order=False,
        label="Structured Hybrid — return_c_distance=True",
        problem_type="OUT:HPP",
    )

if __name__ == "__main__":
    test_find_outliers_hybrid()
    test_find_outliers_hybrid_structured()