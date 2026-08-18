import numpy as np
from typing import Literal, Dict, Tuple, List

from libraries.utils.algorithm.solvers.greedy import greedy_hpp_denn, greedy_hpp_cheapest_insertion, greedy_hpp_algorithm
from libraries.utils.algorithm.solvers.ortools import _hpp_ortools
from libraries.utils.algorithm.solvers.exact_solvers import exact_hpp_held_karp
from libraries.config import HPP_SOLVERS

def hpp_solve(
    D: np.ndarray,
    solver: HPP_SOLVERS = "ortools",
    fixed_endpoints: Dict[str, int | None] | None = None,
    ortools_time_limit: int = 5,
    initial_point_method: Dict | None = None,
    deterministic: bool = True
    ) -> Tuple[List[int], float]:
    """
    Unified HPP solver with multiple backend options (open routes).
    ----------
    Parameters
    ----------
    D : Asymmetric distance matrix.
    solver : Solver.
        - "greedy"             : Single-ended nearest neighbor
        - "greedy_denn"        : Double-ended nearest neighbor (DENN)
        - "cheapest_insertion" : Greedy cheapest insertion (HPP)
        - "ortools"            : OR-Tools with candidate logic
        - "exact"              : Exact Held–Karp DP (REFERENCE ONLY).
                                 Exponential time O(n^2·2^n).
                                 Not suitable for production use.
    fixed_endpoints : {"start": int | None, "end": int | None}
        Optional fixed start/end constraints.
    ortools_time_limit : int
        Time limit for OR-Tools.
    initial_point_method : dict | None
        Endpoint candidate method for OR-Tools.

    -------
    Returns
    -------
    route_order : Visiting order for the HPP path.
    L_opt : Total path length (open route).
    """
    if fixed_endpoints is None:
        fixed_endpoints = {"start": None, "end": None}

    if initial_point_method is None:
        initial_point_method = {"method": "GREEDY_DNN"}
    # --------------------------------------------------
    # Greedy (direct, very fast)
    # --------------------------------------------------
    if solver == "greedy":
        return greedy_hpp_algorithm(D, fixed_endpoints)
    
    # --------------------------------------------------
    # Greedy DENN (direct, very fast)
    # --------------------------------------------------
    if solver == "greedy_denn":
        return greedy_hpp_denn(D, fixed_endpoints)

    # --------------------------------------------------
    # Greedy Cheapest Insertion (direct, higher quality)
    # --------------------------------------------------
    elif solver == "cheapest_insertion":
        return greedy_hpp_cheapest_insertion(D, fixed_endpoints)

    # --------------------------------------------------
    # OR-Tools HPP (high-quality, candidate-based)
    # --------------------------------------------------
    elif solver == "ortools":
        return _hpp_ortools(
            D=D,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            ortools_time_limit=ortools_time_limit,
            deterministic=deterministic
        )
    # --------------------------------------------------
    # Exact DP (Held–Karp) — reference / validation only
    # --------------------------------------------------
    if solver == "exact":
        return exact_hpp_held_karp(D, fixed_endpoints)

    else:
        raise ValueError(f"Unknown solver: {solver}")
