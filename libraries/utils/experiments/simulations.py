import numpy as np
from typing import Tuple, Optional, Dict, Any

def simulate_distance_matrix(
    n: int,
    *,
    seed: Optional[int] = None,
    asymmetry_strength: float = 0.0,
    cluster_strength: float = 0.5,
    outlier_fraction: float = 0.0,
    scale: float = 100.0,
    ) -> np.ndarray:
    """
    Generate a realistic asymmetric distance matrix for routing experiments.
    The matrix is based on clustered 2D geometry with optional:
      - asymmetric perturbations
      - distant outlier nodes
    ----------
    Parameters
    n : Number of nodes.
    seed : Random seed for reproducibility.
    asymmetry_strength : Magnitude of directional noise added to distances (0 = symmetric).
    cluster_strength : Controls how strongly nodes cluster (0 = uniform, 1 = tight clusters).
    outlier_fraction : Fraction of nodes placed far away to create long edges.
    scale : Overall distance scale (larger = longer distances).
    -------
    Returns:
    D : Asymmetric n×n distance matrix with D[i, i] = 0.
    """
    rng = np.random.default_rng(seed)
    # -------------------------------------------------
    # 1) Generate clustered 2D coordinates
    # -------------------------------------------------
    num_clusters = max(1, int(np.sqrt(n)))
    cluster_centers = rng.uniform(0, scale, size=(num_clusters, 2))
    cluster_ids = rng.integers(0, num_clusters, size=n)
    coords = (
        cluster_centers[cluster_ids]
        + rng.normal(scale=cluster_strength * scale / 10, size=(n, 2))
    )
    # -------------------------------------------------
    # 2) Inject outlier nodes (far away)
    # -------------------------------------------------
    num_outliers = int(n * outlier_fraction)
    if num_outliers > 0:
        coords[:num_outliers] += rng.uniform(
            3 * scale, 6 * scale, size=(num_outliers, 2)
        )
    # -------------------------------------------------
    # 3) Compute symmetric Euclidean distances
    # -------------------------------------------------
    diff = coords[:, None, :] - coords[None, :, :]
    D = np.linalg.norm(diff, axis=2)
    # -------------------------------------------------
    # 4) Add controlled asymmetry
    # -------------------------------------------------
    if asymmetry_strength > 0:
        asym = rng.uniform(
            0.0,
            asymmetry_strength * scale,
            size=(n, n),
        )
        np.fill_diagonal(asym, 0.0)
        D = D + asym
    # -------------------------------------------------
    # 5) Final cleanup
    # -------------------------------------------------
    np.fill_diagonal(D, 0.0)
    return D

def simulate_addresses(
    n: int,
    *,
    seed: Optional[int] = None,
    asymmetry_strength: float = 0.0,
    cluster_strength: float = 0.5,
    outlier_fraction: float = 0.0,
    scale: float = 100.0,
    min_postboxes: int = 1,
    max_postboxes: int = 10,
    E: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, np.ndarray] | Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate:
        - an asymmetric n x n distance matrix
        - a postbox vector with occasional outliers
        - (optionally) an address-specific revenue vector E_vec
    ----------
    Parameters:
        n : Number of addresses (nodes)
        seed : Random seed for reproducibility
        asymmetry_strength : Controls how asymmetric the matrix becomes
        cluster_strength : Controls spatial clustering of addresses
        outlier_fraction : Fraction of nodes that are distance outliers
        scale : Overall distance scale
        min_postboxes, max_postboxes : Range for postboxes per address
        E : None OR dict specifying revenue generation
    ----------
    Returns:
        D : Asymmetric distance matrix
        p : Postboxes per address
        E_vec : Address-specific revenue vector (if E is provided)
    """
    # -------------------------------------------------
    # 1) Distance matrix (delegated)
    # -------------------------------------------------
    D = simulate_distance_matrix(
        n=n,
        seed=seed,
        asymmetry_strength=asymmetry_strength,
        cluster_strength=cluster_strength,
        outlier_fraction=outlier_fraction,
        scale=scale,
    )
    # -------------------------------------------------
    # 2) RNG for node attributes
    # -------------------------------------------------
    rng = np.random.default_rng(seed)
    # -------------------------------------------------
    # 3) Generate postboxes
    # -------------------------------------------------
    p = rng.integers(min_postboxes, max_postboxes, size=n)
    num_outliers = int(n * outlier_fraction)
    if num_outliers > 0:
        p[:num_outliers] = rng.integers(
            max(min_postboxes, 2),
            max_postboxes,
            size=num_outliers,
        )
    if E is None:
        return D, p
    # -------------------------------------------------
    # 4) Revenue vector (optional)
    # -------------------------------------------------
    if not isinstance(E, dict) or "val" not in E or "deviation" not in E:
        raise ValueError(
            "E must be None or a dict with keys: {'val', 'deviation', 'seed' (optional)}"
        )
    base = float(E["val"])
    delta = float(E["deviation"])
    E_seed = E.get("seed", seed)
    rng_E = np.random.default_rng(E_seed)
    noise = rng_E.uniform(-delta, +delta, size=n)
    E_vec = np.maximum(base + noise, 0.0)
    return D, p, E_vec