import numbers
import numpy as np
from typing import List

from libraries.config import HYBRID_METHODS
from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.experiments.simulations_structured_route import simulate_structured_route
from libraries.utils.algorithm.single_route.route_solver import solve_route
from libraries.utils.algorithm.single_route.route_solver_structured import solve_structured_route
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data
from libraries.utils.algorithm.structural_heuristics.hybrid_candidate_generation import run_hybrid_candidate_generation

def _run_hybrid_case_non_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    methods: List[HYBRID_METHODS],
    n: int = 8,
    solver: str = "ortools",
    precheck: bool = True,
    ):
    print("\n====================================================")
    print(f"TEST HYBRID (NON-STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  methods={methods}")
    print(f"  precheck={precheck}")
    print("====================================================")
    D, p = simulate_addresses(
        n=n,
        seed=123,
        asymmetry_strength=0.1,
        outlier_fraction=0.1,
    )
    R = list(range(n))
    E = 5.0
    APR = 0.05
    z = 0.0
    L_u = 0.0
    R_seq, L_R = solve_route(
        D=D,
        R=R,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        L_u=L_u,
        deterministic=True,
        ortools_time_limit=3,
    )
    C_distance = {}
    C2 = {}
    R_map = {}
    (
        C_distance,
        C2,
        R_map,
        inner_cache,
        outer_cache,
    ) = run_hybrid_candidate_generation(
        D=D,
        R=R,
        R_seq=R_seq,
        p=p,
        E=E,
        APR=APR,
        z=z,
        strict_order=strict_order,
        L_R=L_R,
        L_u=L_u,
        problem_type=problem_type,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        methods=methods,
        A_kwargs={},
        B_kwargs={},
        U_kwargs={},
        precheck=precheck,
        k_all=1,
        k_max=4,
        B=10,
        C_distance=C_distance,
        C2=C2,
        R_map=R_map,
    )

    assert isinstance(C_distance, dict)
    assert isinstance(C2, dict)
    assert isinstance(R_map, dict)
    for S in C2:
        assert isinstance(S, frozenset)
        assert S in C_distance
    for v in C2.values():
        assert isinstance(v, numbers.Real)
    assert inner_cache in ({}, None)
    assert outer_cache in ({}, None)

def test_hybrid_candidate_generation_non_structured():
    _run_hybrid_case_non_structured(
        label="Type 1 — TSP — all methods",
        strict_order=True,
        problem_type="TSP",
        methods=["A", "B", "Beam"],
    )
    _run_hybrid_case_non_structured(
        label="Type 2 — TSP — Beam only",
        strict_order=False,
        problem_type="TSP",
        methods=["Beam"],
    )
    _run_hybrid_case_non_structured(
        label="Type 2 — HPP — A + B",
        strict_order=False,
        problem_type="HPP",
        methods=["A", "B"],
        solver="greedy_denn",
    )
    _run_hybrid_case_non_structured(
        label="Type 2 — HPP — Empty",
        strict_order=False,
        problem_type="HPP",
        methods=[],
        solver="greedy_denn",
    )
    _run_hybrid_case_non_structured(
        label="HPP — Type 1 — U only",
        strict_order=True,
        problem_type="HPP",
        methods=["U"],
    )
    _run_hybrid_case_non_structured(
        label="HPP — Type 2 — Beam + U",
        strict_order=False,
        problem_type="HPP",
        methods=["Beam", "U"],
        solver="greedy",
    )
    _run_hybrid_case_non_structured(
        label="TSP — Type 2 — A + B + U",
        strict_order=False,
        problem_type="TSP",
        methods=["A", "B", "U"],
        solver="greedy",
    )
    _run_hybrid_case_non_structured(
        label="TSP — Type 2 — A + B + Beam + U",
        strict_order=False,
        problem_type="TSP",
        methods=["A", "B", "Beam", "U"],
        solver="greedy",
    )

def _run_hybrid_case_structured(
    *,
    label: str,
    strict_order: bool,
    problem_type: str,
    methods: List[HYBRID_METHODS],
    n_units: int = 4,
    solver: str = "ortools",
    precheck: bool = True,
    ):
    print("\n====================================================")
    print(f"TEST HYBRID (STRUCTURED): {label}")
    print(f"  strict_order={strict_order}")
    print(f"  problem_type={problem_type}")
    print(f"  methods={methods}")
    print(f"  precheck={precheck}")
    print("====================================================")

    D_big, nodes, p = simulate_structured_route(
        n_units=n_units,
        min_unit_size=2,
        max_unit_size=3,
        seed=2024,
        asymmetry_strength=0.1,
    )
    D_outer, inner_models, D_all = build_structured_route_data(
        D_big=D_big,
        nodes=nodes,
    )
    R = sorted(a for m in inner_models for a in m["route_nodes_global"])
    E = 5.0
    APR = 0.05
    z = 0.0
    L_u = 0.0
    R_seq, L_R, inner_cache, outer_cache = solve_structured_route(
        D_outer=D_outer,
        D_all=D_all,
        R=R,
        inner_models=inner_models,
        strict_order=strict_order,
        problem_type=problem_type,
        solver=solver,
        deterministic=True,
        ortools_time_limit=3,
    )
    C_distance = {}
    C2 = {}
    R_map = {}
    (   C_distance,
        C2,
        R_map,
        inner_cache,
        outer_cache,
    ) = run_hybrid_candidate_generation(
        D=D_outer,
        R=R,
        R_seq=R_seq,
        p=p,
        E=E,
        APR=APR,
        z=z,
        strict_order=strict_order,
        L_R=L_R,
        L_u=L_u,
        problem_type=problem_type,
        deterministic=True,
        solver=solver,
        ortools_time_limit=3,
        methods=methods,
        A_kwargs={},
        B_kwargs={},
        precheck=precheck,
        k_all=1,
        k_max=4,
        B=10,
        C_distance=C_distance,
        C2=C2,
        R_map=R_map,
        D_all=D_all,
        inner_models=inner_models,
        inner_cache=inner_cache,
        outer_cache=outer_cache,
    )

    # ---------------- Validation ----------------
    assert isinstance(C_distance, dict)
    assert isinstance(C2, dict)
    assert isinstance(R_map, dict)
    for S in C2:
        assert isinstance(S, frozenset)
        assert S in C_distance
    for v in C2.values():
        assert isinstance(v, numbers.Real)
    assert isinstance(inner_cache, dict)
    assert isinstance(outer_cache, dict)

def test_hybrid_candidate_generation_structured():
    _run_hybrid_case_structured(
        label="OUT:HPP — Type 1 — all methods",
        strict_order=True,
        problem_type="OUT:HPP",
        methods=["A", "B", "Beam"],
    )
    _run_hybrid_case_structured(
        label="OUT:HPP — Type 2 — Beam only",
        strict_order=False,
        problem_type="OUT:HPP",
        methods=["Beam"],
        solver="greedy",
    )
    _run_hybrid_case_structured(
        label="OUT:TSP — Type 2 — A + B",
        strict_order=False,
        problem_type="OUT:TSP",
        methods=["A", "B"],
        solver="greedy",
    )
    _run_hybrid_case_structured(
        label="OUT:TSP — Type 2 — []",
        strict_order=False,
        problem_type="OUT:TSP",
        methods=[],
        solver="greedy",
    )
    _run_hybrid_case_structured(
        label="OUT:HPP — Type 1 — U only",
        strict_order=True,
        problem_type="OUT:HPP",
        methods=["U"],
    )
    _run_hybrid_case_structured(
        label="OUT:HPP — Type 2 — Beam + U",
        strict_order=False,
        problem_type="OUT:HPP",
        methods=["Beam", "U"],
        solver="greedy",
    )
    _run_hybrid_case_structured(
        label="OUT:TSP — Type 2 — A + B + U",
        strict_order=False,
        problem_type="OUT:TSP",
        methods=["A", "B", "U"],
        solver="greedy",
    )
    _run_hybrid_case_structured(
        label="OUT:TSP — Type 2 — A + B + Beam + U",
        strict_order=False,
        problem_type="OUT:TSP",
        methods=["A", "B", "Beam", "U"],
        solver="greedy",
    )

if __name__ == "__main__":
    test_hybrid_candidate_generation_non_structured()
    test_hybrid_candidate_generation_structured()
