from typing import List, Tuple, Literal
import numpy as np

from libraries.utils.algorithm.solvers.tsp import tsp_solve
from libraries.utils.algorithm.solvers.hpp import hpp_solve
from libraries.utils.algorithm.solvers.type1 import route_length_type1
from libraries.config import PROBLEM_TYPES, SOLVERS

def solve_route(
    D: np.ndarray,
    R: List[int],
    *,
    strict_order: bool,
    problem_type: PROBLEM_TYPES = "TSP",
    L_u: float | List[float] | np.ndarray = 0.0,
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    ortools_time_limit: int = 5,
    fixed_endpoints=None,
    initial_point_method=None,
    ) -> Tuple[List[int], float]:
    """
    Solve a route for a given set of nodes.
    ----------
    Parameters
    ----------
    D : Asymmetric distance matrix for the nodes in R.
    R : List of node indices defining the route.
    strict_order :
        If True, the visiting order is fixed (Type 1).
        If False, the route order is optimized (Type 2).
    problem_type : {"TSP", "HPP"}
        "TSP" = closed route,
        "HPP" = open route.
    L_u : Internal lengths per route unit (scalar or vector).
    deterministic : If True, a deterministic solver is used.
    solver :Solver backend used for optimized routes.
    ortools_time_limit : Time limit (in seconds) for OR-Tools based solvers.
    fixed_endpoints : Fixed start/end points (HPP only).
    initial_point_method : Initialization method for open routes (HPP only).
    
    ----------
    Returns
    ----------
    R_seq : Ordered route as a list of node indices.
    L : Total route length.
    """

    if strict_order:
        R_seq = list(R)
        L = route_length_type1(
            D,
            R_seq,
            L_u=L_u,
            problem_type=problem_type,
        )
        return R_seq, L
    if problem_type == "TSP":
        order, L = tsp_solve(
            D,
            deterministic_tsp=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
        )
    elif problem_type == "HPP":
        order, L = hpp_solve(
            D,
            solver=solver,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            ortools_time_limit=ortools_time_limit,
            deterministic=deterministic
        )
    else:
        raise ValueError(f"Unknown problem_type: {problem_type}")
    R_seq = [R[i] for i in order]
    if isinstance(L_u, (int, float, np.floating, np.integer)):
        L += float(L_u) * len(R_seq)
    return R_seq, L
