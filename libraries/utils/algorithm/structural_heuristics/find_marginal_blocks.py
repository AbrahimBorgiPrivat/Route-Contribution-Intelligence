import numpy as np
from typing import FrozenSet, List

def find_marginal_blocks(
        D: np.ndarray,
        p: List[int],
        E: float | List[float] | np.ndarray,
        APR: float,
        z: float = 0.0,
        R: List[int] = None,
        L_u: float | List[float] | np.ndarray = 0.0,
        L_max: int = 10,
        k_min: int = 1,
    ) -> List[FrozenSet[int]]:
    """
    Method B: Detect marginally weak blocks along the route R_seq.
    Uses Type 1 marginal approximation for each address and extends blocks while cumulative margin >= z.
    ----------
    Parameters
    D : Distance matrix.
    R_seq : Route sequence (Type 1 fixed order or Type 2 TSP order).
    p : Postboxes per address.
    E : float med gns. enhedspris eller liste/array med individuelle enhedspriser pr. adresse.
    APR : Distance cost per km.
    z : Candidate threshold for cumulative marginal block.
    L_max : Maximum block size to consider.
    -------
    Returns Candidate marginal blocks S where sum C2({c}) >= z.
    """
    if R is None:
        R = list(range(D.shape[0]))
    n = len(R)
    D = np.asarray(D)
    p = np.asarray(p)
    # ------------------------------------------------------------
    # Handle scalar vs. vector E
    # ------------------------------------------------------------
    if isinstance(E, (float, int, np.floating, np.integer)):
        E_vec = None
    else:
        E_vec = np.asarray(E, dtype=float)
        if len(E_vec) != len(p):
            raise ValueError("Length of E must match length of p when E is a vector.")
    # ------------------------------------------------------------
    # Handle scalar vs vector L_u
    # ------------------------------------------------------------
    if isinstance(L_u, (float, int, np.floating, np.integer)):
        L_u_vec = None
    else:
        L_u_vec = np.asarray(L_u, dtype=float)
        if len(L_u_vec) != len(p):
            raise ValueError("Length of L_u must match length of p when L_u is a vector.")
    # ------------------------------------------------------------
    # Compute marginal C2 per node
    # ------------------------------------------------------------
    delta_C2 = np.zeros(len(p), dtype=float)
    for idx in range(n):
        c = R[idx]
        l = R[(idx - 1) % n]
        r = R[(idx + 1) % n]
        dL = -D[l, c] - D[c, r] + D[l, r]
        inner = L_u if L_u_vec is None else L_u_vec[c]
        if E_vec is None:
            revenue_loss = float(E) * p[c]
        else:
            revenue_loss = E_vec[c] * p[c]
        delta_C2[c] = -revenue_loss - APR * (dL - inner)
    # ------------------------------------------------------------
    # Accumulate contiguous blocks
    # ------------------------------------------------------------
    candidates = set()
    for i in range(n):
        cum = 0.0
        S = set()
        for k in range(L_max):
            j = (i + k) % n
            node = R[j]
            cum += delta_C2[node]
            S.add(node)
            if len(S) >= k_min and cum >= z:
                candidates.add(frozenset(S))
    return list(candidates)