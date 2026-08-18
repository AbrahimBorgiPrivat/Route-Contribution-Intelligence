import numpy as np

def inner_length(
    R: list[int],
    route: list[int],
    L_u: float | list[float] | np.ndarray = 0.0,
    ) -> float:
    """
    Compute total inner length for a route that is a (possibly reduced)
    ordering of the original route R.
    ----------
    Parameters
    ----------
    R     : Original route defining the index space of L_u.
    route : Visiting order (subset and permutation of R).
    L_u : 
        - Scalar: same inner length for all units
        - Vector: per-unit inner length defined over R
    ----------
    Returns
    ----------
    float
        Sum of inner lengths for the given route.
    """
    n = len(route)
    if n == 0:
        return 0.0
    if isinstance(L_u, (int, float, np.floating, np.integer)):
        return float(L_u) * n
    L_u_arr = np.asarray(L_u, dtype=float)
    idx = [R.index(u) for u in route]
    return float(np.sum(L_u_arr[idx]))

def _to_pylist(route):
    "Ensure int structure for route"
    return [int(x) for x in route]