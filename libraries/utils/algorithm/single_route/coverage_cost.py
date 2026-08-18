import numpy as np
from typing import List, Set

def compute_rute_covarage(
    E: float | List[float] | np.ndarray,
    APR: float,
    p: List[int] | np.ndarray,
    L_R: float,
    L_u: float | List[float] | np.ndarray = 0.0,
    ) -> float:
    """
    Compute route coverage (dækningsgrad).
    ----------
    Parameters
    ----------
    E   : Revenue per postbox (scalar or per-address).
    APR : Cost per unit distance.
    p   : Number of postboxes per address.
    L_R : Edge-based route length.
    L_u : Inner lengths per address (scalar or vector).

    
    -------
    Returns
    -------
        Route coverage DG(R).
    """
    p_arr = np.asarray(p, dtype=float)
    if isinstance(E, (float, int, np.floating, np.integer)):
        revenue = float(E) * float(np.sum(p_arr))
    else:
        E_arr = np.asarray(E, dtype=float)
        if len(E_arr) != len(p_arr):
            raise ValueError("Length of E must match length of p when E is vector-valued.")
        revenue = float(np.sum(E_arr * p_arr))
    if isinstance(L_u, (float, int, np.floating, np.integer)):
        inner = float(L_u) * len(p_arr)
    else:
        L_u_arr = np.asarray(L_u, dtype=float)
        if len(L_u_arr) != len(p_arr):
            raise ValueError("Length of L_u must match length of p when L_u is vector-valued.")
        inner = float(np.sum(L_u_arr))
    return revenue - APR * (float(L_R) + inner)

def compute_coverage_change(
        E: float | List[float] | np.ndarray,
        APR: float,
        p: List[int],
        R: List[int],
        S: Set[int],
        C: float
    ) -> float:
    """
    Beregner ændringen i dækningsgrad (C2 eller C2*).
    ----------
    Parameters
    ----------
        E : float med gns. enhedspris eller liste/array med individuelle enhedspriser pr. adresse pr. postkasse.
    APR : Omkostning pr. kilometer (afstandspris)
    p : Antal postkasser pr. adresse
    R : Den oprindelige rute (liste af adresser)
    S : Delmængde af adresser, der fjernes
    C : Ændringen i rutelængde (fra Delalgoritme 1)
    
    -------
    Returns
    -------
    C2 : Ændringen i dækningsgrad
    """
    p = np.array(p)
    R_reduced = [i for i in R if i not in S]
    # ------------------------------------------------------------
    # Case 1: E is a simple float (global revenue model)
    # ------------------------------------------------------------
    if isinstance(E, (float, int, np.floating, np.integer)):
        N_R = np.sum(p[R])
        N_R_reduced = np.sum(p[R_reduced])
        return E * (N_R_reduced - N_R) - APR * C
    # ------------------------------------------------------------
    # Case 2: E is address-specific (vector)
    # ------------------------------------------------------------
    E = np.array(E, dtype=float)
    if len(E) != len(p):
        raise ValueError("Length of E must match length of p when E is a vector.")
    revenue_R = np.sum(E[R] * p[R])
    revenue_R_reduced = np.sum(E[R_reduced] * p[R_reduced])
    return (revenue_R_reduced - revenue_R) - APR * C