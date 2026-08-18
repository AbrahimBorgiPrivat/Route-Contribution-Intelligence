from itertools import combinations
import numpy as np
from typing import List, FrozenSet, Optional, Literal

def estimate_tsp_threshold(
    D: np.ndarray,
    R_seq: List[int] = None,
    method: Optional[Literal["kneedle", "relative"]] = None,
    min_rel_jump: float = 2.0,
    ) -> float:
    """
    D : Distance matrix (n x n).
    R_seq : Route order (e.g. optimal TSP tour over all nodes).
    method : Threshold estimation method.
        - None or "kneedle": use Kneedle-style knee detection on sorted edges.
        - "relative": use first large relative jump in sorted edges.
    min_rel_jump : Only used when method == "relative".
        Minimum ratio L[i+1] / L[i] to consider a jump significant.
    -------
    Returns : Threshold distance (same units as D).
    """
    n = D.shape[0]
    if R_seq is None:
        R_seq = list(range(n))
    edges = []
    m = len(R_seq)
    for i in range(m):
        a = R_seq[i]
        b = R_seq[(i + 1) % m]  # wrap to form a tour
        edges.append(D[a, b])
    edges = np.asarray(edges, dtype=float)
    L = np.sort(edges)
    if len(L) == 0:
        raise ValueError("No edges found in R_seq; cannot estimate threshold.")
    if np.allclose(L, L[0]):
        return float(L[0])
    # ----------------------------------------------------------------------
    # Method 1: Kneedle (default if method is None or "kneedle")
    # ----------------------------------------------------------------------
    if method is None or method == "kneedle":
        n = len(L)
        x = np.linspace(0.0, 1.0, n)
        L_min, L_max = L[0], L[-1]
        y = (L - L_min) / (L_max - L_min + 1e-12)
        g = x
        diff = g - y
        mask = diff > 0
        if not np.any(mask):
            # No positive region: fall back to median as a conservative choice
            return float(np.median(L))
        max_val = diff[mask].max()
        idx_candidates = np.where(diff == max_val)[0]
        idx = int(idx_candidates.max())
        return float(L[idx])
    # ----------------------------------------------------------------------
    # Method 2: Relative jump in sorted edges
    # ----------------------------------------------------------------------
    elif method == "relative":
        ratios = L[1:] / (L[:-1] + 1e-12)
        jump_indices = np.where(ratios >= min_rel_jump)[0]
        if len(jump_indices) > 0:
            i = int(jump_indices[0])
            return float(L[i])
        return float(np.median(L) * 2.0)
    else:
        raise ValueError(f"Unknown method: {method!r}")


def greedy_peripheral_clusters(
    D: np.ndarray,
    R: List[int] = None,
    k_min: int = 1,
    k_max: int = None,
    method: Optional[Literal["kneedle", "relative"]] = None,
    min_rel_jump: float = None,
    combine_clusters: bool = True
    ) -> List[FrozenSet[int]]:
    """
    Greedy clustering using TSP edge median as local scale.
    ----------
    Parameters
    D : Distance matrix.
    R : Route sequence (Type 1 fixed order or Type 2 TSP order).
    k_min: Minimum cluster size.
    k_max: Maximum cluster size.
    method : Threshold estimation method.
    min_rel_jump : Minimum relative jump for threshold estimation (only relevant for method = 'relative').
    combine_clusters : Whether to combine pairs of clusters into larger clusters if within size limits.
    -------
    Returns List of clusters
    """
    n = D.shape[0]
    if k_max is None:
        k_max = n//2
    nodes = set(range(n))
    D = np.asarray(D)
    threshold = estimate_tsp_threshold(D, R_seq=R, method=method, min_rel_jump=min_rel_jump)
    clusters = []
    while nodes:
        i = next(iter(nodes))
        S = {i}
        nodes.remove(i)
        while True:
            remaining = list(nodes)
            if not remaining:
                break
            dists = np.array([min(D[s,j] for s in S) for j in remaining])
            j_idx = np.argmin(dists)
            j = remaining[j_idx]
            dmin = dists[j_idx]
            if dmin > threshold:
                break
            S.add(j)
            nodes.remove(j)
        if k_min <= len(S) <= k_max:
            clusters.append(frozenset(S))
    if combine_clusters and len(clusters) >= 2:
        combined = set()
        for S1, S2 in combinations(clusters, 2):
            U = S1.union(S2)
            if k_min <= len(U) <= k_max:
                combined.add(frozenset(U))
        clusters = list(set(clusters).union(combined))
    return clusters