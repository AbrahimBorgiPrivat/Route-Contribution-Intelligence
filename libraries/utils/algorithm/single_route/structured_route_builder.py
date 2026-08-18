import numpy as np
from typing import List, Dict, Tuple


def build_structured_route_data(
    D_big: np.ndarray,
    nodes: List[Dict],
    ) -> Tuple[np.ndarray, List[Dict], np.ndarray]:
    """
    Build structured routing data from a flat distance matrix.

    ----------
    Parameters
    ----------
    D_big :
        Full distance matrix over ALL nodes (addresses + unit start/end nodes),
        indexed by node["m_index"].
    nodes :
        List of node descriptors. Each node MUST contain:
            - "m_index": int
                Index into D_big.
            - "unit": int
                GLOBAL unit / segment identifier.
                Must be stable across reductions.
            - "type": {"start", "end", "address"}
                Role of the node within its unit.
            - "route_number": int | None
                GLOBAL address identifier.
                Must be set for address nodes.
                Must be None for start/end nodes.
        For each unit:
            - exactly one "start" node
            - exactly one "end" node
            - zero or more "address" nodes
        route_number values must be unique across all address nodes.

    -------
    Returns
    -------
    D_outer :
        Unit-to-unit distance matrix (exit -> entry), indexed by LOCAL outer indices (0..n_units-1).
    inner_models : List of structured inner models (one per unit) - containing both LOCAL and GLOBAL identifiers:
            {
                "outer_index": int,              # LOCAL unit index
                "outer_index_global": int,       # GLOBAL unit id (stable)
                "route_nodes": List[int],        # LOCAL address ids (initially == GLOBAL)
                "route_nodes_global": List[int], # GLOBAL address ids (stable)
                "D_inner": np.ndarray,           # inner distance matrix
                "entry_index": int,              # index of entry node (0)
                "exit_index": int,               # index of exit node
                "node_map": Dict[int,int],       # inner-local -> LOCAL address id
            }
    D_full :
        Address-to-address distance matrix for structured Type 1,
        indexed by GLOBAL route_number,
        respecting unit boundaries via start/end traversal.
    """

    # --------------------------------------------------
    # 1) Partition nodes by unit
    # --------------------------------------------------
    address_nodes = [n for n in nodes if n["type"] == "address"]
    unit_nodes: Dict[int, Dict] = {}
    for n in nodes:
        u = n["unit"]  # GLOBAL unit id
        unit_nodes.setdefault(u, {"start": None, "end": None, "addresses": []})
        if n["type"] == "start":
            unit_nodes[u]["start"] = n
        elif n["type"] == "end":
            unit_nodes[u]["end"] = n
        elif n["type"] == "address":
            unit_nodes[u]["addresses"].append(n)
        else:
            raise ValueError(f"Unknown node type: {n['type']}")

    unit_ids = sorted(unit_nodes.keys())  # GLOBAL unit ids
    for u, block in unit_nodes.items():
        if block["start"] is None or block["end"] is None:
            raise ValueError(f"Unit {u} must have exactly one start and one end node")

    # --------------------------------------------------
    # 2) Construct D_full (structured Type 1 matrix)
    # --------------------------------------------------
    route_numbers = [n["route_number"] for n in address_nodes]
    if any(r is None for r in route_numbers):
        raise ValueError("All address nodes must have a route_number")

    if len(set(route_numbers)) != len(route_numbers):
        raise ValueError("route_number values must be unique")

    n_addr = max(route_numbers) + 1

    addr_by_route = {
        n["route_number"]: n
        for n in address_nodes
    }

    D_full = np.zeros((n_addr, n_addr), dtype=float)
    for i in range(n_addr):
        ni = addr_by_route[i]
        mi = ni["m_index"]
        ui = ni["unit"]
        end_i = unit_nodes[ui]["end"]["m_index"]
        for j in range(n_addr):
            nj = addr_by_route[j]
            mj = nj["m_index"]
            uj = nj["unit"]
            if ui == uj:
                D_full[i, j] = D_big[mi, mj]
            else:
                start_j = unit_nodes[uj]["start"]["m_index"]
                D_full[i, j] = (
                    D_big[mi, end_i]
                    + D_big[end_i, start_j]
                    + D_big[start_j, mj]
                )

    # --------------------------------------------------
    # 3) Construct D_outer (unit -> unit)
    # --------------------------------------------------
    n_units = len(unit_ids)
    D_outer = np.zeros((n_units, n_units), dtype=float)
    for i, ui in enumerate(unit_ids):
        end_i = unit_nodes[ui]["end"]["m_index"]
        for j, uj in enumerate(unit_ids):
            if i == j:
                D_outer[i, j] = 0.0
            else:
                start_j = unit_nodes[uj]["start"]["m_index"]
                D_outer[i, j] = D_big[end_i, start_j]

    # --------------------------------------------------
    # 4) Construct inner_models (structured Type 2)
    # --------------------------------------------------
    inner_models: List[Dict] = []
    for local_outer_idx, u_global in enumerate(unit_ids):
        block = unit_nodes[u_global]
        start = block["start"]
        end = block["end"]
        addresses = sorted(
            block["addresses"],
            key=lambda x: x["route_number"],
        )
        local_nodes = [start] + addresses + [end]
        local_indices = [n["m_index"] for n in local_nodes]
        D_inner = D_big[np.ix_(local_indices, local_indices)]
        route_nodes_global = [addr["route_number"] for addr in addresses]
        route_nodes_local = route_nodes_global.copy()
        node_map = {
            i + 1: addr_local
            for i, addr_local in enumerate(route_nodes_local)
        }
        inner_models.append({
            "outer_index": local_outer_idx,
            "route_nodes": route_nodes_local,
            "outer_index_global": u_global,
            "route_nodes_global": route_nodes_global,
            "D_inner": D_inner,
            "entry_index": 0,
            "exit_index": len(local_nodes) - 1,
            "node_map": node_map,
        })

    return D_outer, inner_models, D_full