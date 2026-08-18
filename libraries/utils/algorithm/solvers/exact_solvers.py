from typing import Optional, Dict, List, Tuple
import numpy as np
from libraries.utils.algorithm.solvers.common import _to_pylist

def exact_tsp_held_karp(D: np.ndarray) -> Tuple[List[int], float]:
    """
    Exact TSP solver using Held–Karp dynamic programming.
    ----------
    Parameters
    ----------
    D : Asymmetric distance matrix (n x n).
    
    ----------
    Returns
    ----------
    tour : Optimal TSP tour (cycle, starting at 0).
    L_opt : Optimal tour length.
    """
    n = len(D)
    N = 1 << n
    dp = np.full((N, n), np.inf)
    parent = np.full((N, n), -1, dtype=int)
    dp[1, 0] = 0.0  
    for mask in range(N):
        if not (mask & 1):
            continue
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            prev_mask = mask ^ (1 << j)
            if prev_mask == 0 and j == 0:
                continue
            for k in range(n):
                if prev_mask & (1 << k):
                    cost = dp[prev_mask, k] + D[k, j]
                    if cost < dp[mask, j]:
                        dp[mask, j] = cost
                        parent[mask, j] = k
    full_mask = N - 1
    best_len = np.inf
    last = -1
    for j in range(1, n):
        cost = dp[full_mask, j] + D[j, 0]
        if cost < best_len:
            best_len = cost
            last = j
    tour = []
    mask = full_mask
    j = last
    while j != -1:
        tour.append(j)
        pj = parent[mask, j]
        mask ^= (1 << j)
        j = pj
    tour.reverse()
    return _to_pylist(tour), float(best_len)

def exact_hpp_held_karp(
    D: np.ndarray,
    fixed_endpoints: Optional[Dict[str, int | None]] = None,
    ) -> Tuple[List[int], float]:
    """
    Exact Hamiltonian Path solver via Held–Karp DP.
    ----------
    D : Asymmetric distance matrix.
    fixed_endpoints : {"start": int | None, "end": int | None}
    ----------
    Returns
    path : Optimal visiting order (open path).
    L_opt : Optimal path length.
    """
    n = len(D)
    if fixed_endpoints is None:
        fixed_endpoints = {"start": None, "end": None}
    start_fixed = fixed_endpoints.get("start")
    end_fixed = fixed_endpoints.get("end")
    N = 1 << n
    dp = np.full((N, n), np.inf)
    parent = np.full((N, n), -1, dtype=int)

    for i in range(n):
        if start_fixed is None or i == start_fixed:
            dp[1 << i, i] = 0.0
    for mask in range(N):
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            prev_mask = mask ^ (1 << j)
            if prev_mask == 0:
                continue
            for k in range(n):
                if prev_mask & (1 << k):
                    cost = dp[prev_mask, k] + D[k, j]
                    if cost < dp[mask, j]:
                        dp[mask, j] = cost
                        parent[mask, j] = k
    full_mask = N - 1
    best_len = np.inf
    last = -1
    for j in range(n):
        if end_fixed is not None and j != end_fixed:
            continue
        if dp[full_mask, j] < best_len:
            best_len = dp[full_mask, j]
            last = j
    path = []
    mask = full_mask
    j = last
    while j != -1:
        path.append(j)
        pj = parent[mask, j]
        mask ^= (1 << j)
        j = pj
    path.reverse()
    return _to_pylist(path), float(best_len)