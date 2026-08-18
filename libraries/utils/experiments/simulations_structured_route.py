import numpy as np
from typing import List, Dict, Tuple, Optional


def simulate_structured_route(
    n_units: int,
    *,
    min_unit_size: int = 1,
    max_unit_size: int = 5,
    seed: Optional[int] = None,
    asymmetry_strength: float = 0.0,
    cluster_strength: float = 0.5,
    outlier_fraction: float = 0.0,
    scale: float = 100.0,
    min_postboxes: int = 1,
    max_postboxes: int = 10,
) -> Tuple[np.ndarray, List[Dict], np.ndarray]:
    """
    Generate a flat structured routing instance.

    Returns:
    :-------:
        - D_big : (n_addresses + 2*n_units) x (n_addresses + 2*n_units)
        - nodes : list of node descriptors compatible with build_structured_route_data
        {
            "m_index": int,                 # index into D_big
            "unit": int,                    # GLOBAL unit id
            "type": "start" | "address" | "end",
            "route_number": int | None,     # only for address nodes
        }
        - p     : postboxes per address (indexed by route_number)
    """
    rng = np.random.default_rng(seed)
    # ==================================================
    # 1) Decide unit sizes
    # ==================================================
    unit_sizes = rng.integers(
        min_unit_size,
        max_unit_size + 1,
        size=n_units,
    )
    n_addresses = int(unit_sizes.sum())
    # ==================================================
    # 2) Generate unit-level geometry
    # ==================================================
    num_clusters = max(1, int(np.sqrt(n_units)))
    cluster_centers = rng.uniform(0, scale, size=(num_clusters, 2))
    cluster_ids = rng.integers(0, num_clusters, size=n_units)
    unit_centers = (
        cluster_centers[cluster_ids]
        + rng.normal(scale=cluster_strength * scale / 10, size=(n_units, 2))
    )
    n_outliers = int(outlier_fraction * n_units)
    if n_outliers > 0:
        unit_centers[:n_outliers] += rng.uniform(
            3 * scale, 6 * scale, size=(n_outliers, 2)
        )
    # ==================================================
    # 3) Build nodes + coordinates
    # ==================================================
    nodes: List[Dict] = []
    coords: List[np.ndarray] = []
    m_index = 0
    route_number = 0
    for unit_id, unit_size in enumerate(unit_sizes):
        # ------------------------------
        # Start node
        # ------------------------------
        nodes.append({
            "m_index": m_index,
            "unit": unit_id,
            "type": "start",
            "route_number": None,
        })
        coords.append(
            unit_centers[unit_id]
            + rng.normal(scale=cluster_strength * scale / 20, size=2)
        )
        m_index += 1
        # ------------------------------
        # Address nodes
        # ------------------------------
        for _ in range(unit_size):
            nodes.append({
                "m_index": m_index,
                "unit": unit_id,
                "type": "address",
                "route_number": route_number,
            })
            coords.append(
                unit_centers[unit_id]
                + rng.normal(scale=cluster_strength * scale / 15, size=2)
            )
            route_number += 1
            m_index += 1
        # ------------------------------
        # End node
        # ------------------------------
        nodes.append({
            "m_index": m_index,
            "unit": unit_id,
            "type": "end",
            "route_number": None,
        })
        coords.append(
            unit_centers[unit_id]
            + rng.normal(scale=cluster_strength * scale / 20, size=2)
        )
        m_index += 1
    coords = np.asarray(coords)
    n_total = coords.shape[0]
    # ==================================================
    # 4) Construct D_big
    # ==================================================
    diff = coords[:, None, :] - coords[None, :, :]
    D_big = np.linalg.norm(diff, axis=2)
    if asymmetry_strength > 0.0:
        asym = rng.uniform(
            0.0,
            asymmetry_strength * scale,
            size=(n_total, n_total),
        )
        np.fill_diagonal(asym, 0.0)
        D_big = D_big + asym
    np.fill_diagonal(D_big, 0.0)
    # ==================================================
    # 5) Postboxes per address (indexed by route_number)
    # ==================================================
    p = rng.integers(
        min_postboxes,
        max_postboxes + 1,
        size=n_addresses,
    )
    return D_big, nodes, p
