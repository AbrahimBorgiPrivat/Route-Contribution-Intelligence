import numpy as np
from typing import List, Literal
from libraries.utils.algorithm.solvers.common import inner_length
from libraries.config import PROBLEM_TYPES

def route_length_type1(
    Dmat: np.ndarray,
    route: List[int],
    L_u: float | List[float] | np.ndarray = 0.0,
    problem_type: PROBLEM_TYPES = "TSP",
    ) -> float:
    """
    Compute route length for Type 1 (fixed order).
    ----------
    Parameters: 
    Dmat  : Asymmetric distance matrix.
    route : Fixed visiting order (e.g. [0,1,2,3]).
    L_u   : 
        - Inner length(s). If scalar, applied uniformly.
        - If list/array, must match len(route).
    problem_type 
        - "TSP"  : closed route (return to start)
        - "SHPP" : open route (no return)
    ----------
    Returns:
        Total route length.
    """
    n_nodes = Dmat.shape[0]
    for node in route:
        if node < 0 or node >= n_nodes:
            raise ValueError(f"Route contains index {node}, but Dmat has only {n_nodes} nodes.")
    n = len(route)
    if n == 0:
        return 0.0
    if isinstance(L_u, (int, float, np.floating, np.integer)):
        inner_Lu = float(L_u) * n
    else:
        inner_Lu = inner_length(route, route, L_u)
    if problem_type == "TSP":
        edge_length = sum(Dmat[route[i], route[(i + 1) % n]] for i in range(n))
    elif problem_type == "HPP":
        edge_length = sum(Dmat[route[i], route[i + 1]] for i in range(n - 1))
    else:
        raise ValueError(f"Unknown problem_type: {problem_type}")
    return inner_Lu + edge_length