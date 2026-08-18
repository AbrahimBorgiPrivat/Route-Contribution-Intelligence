from typing import Set, List, Dict, Tuple, Literal, Optional
import numpy as np

from libraries.utils.algorithm.single_route.route_solver import route_length_type1
from libraries.utils.algorithm.solvers.tsp import tsp_solve
from libraries.utils.algorithm.solvers.hpp import hpp_solve
from libraries.config import STRUCTURED_PROBLEM_TYPES, SOLVERS, HPP_SOLVERS

def apply_s_to_structured_model(
    D_outer: np.ndarray,
    D_all: np.ndarray,
    R: List[int],
    inner_models: List[Dict],
    S: Set[int],
    ) -> Tuple[
    np.ndarray,          # D_outer_new
    np.ndarray,          # D_all_new
    List[int],           # R_local_reduced
    List[Dict],          # inner_models_new
    Dict[int, int],      # outer_index_map  (old_local_outer -> new_local_outer)
    Dict[int, int],      # address_index_map (old_global_addr -> new_local_addr)
    ]:
    """
    Apply removal set S to a structured route model.
    - GLOBAL identifiers (outer_index_global, route_nodes_global) are preserved and only FILTERED (never remapped).
    - LOCAL identifiers (outer_index, route_nodes, node_map) are rebuilt.

    ----------
    Parameters
    ----------
    D_outer : Distance between units (exit -> entry).
    D_all : Full address-to-address distance matrix.
    R : Full list of GLOBAL address route_numbers.
    inner_models : List of structured inner models (one per unit).
    S : Set of GLOBAL address route_numbers to remove.

    -------
    Returns
    -------
    D_outer_new : Reduced D_outer after applying S.
    D_all_new : Reduced D_all after applying S.
    R_local_reduced : Reduced list of LOCAL address indices after applying S.
    inner_models_new : Reduced list of structured inner models after applying S.
    outer_index_map : Mapping from OLD LOCAL outer indices to NEW LOCAL outer indices.
    address_index_map : Mapping from OLD GLOBAL address indices to NEW LOCAL address indices.
    """

    D_outer = np.asarray(D_outer, dtype=float)
    D_all = np.asarray(D_all, dtype=float)

    # ==================================================
    # A) Reduce addresses globally (Type 1 + Type 2)
    # ==================================================
    R_reduced = [a for a in R if a not in S]
    address_index_map: Dict[int, int] = {
        old_addr: new_idx for new_idx, old_addr in enumerate(R_reduced)
    }
    R_local_reduced = list(range(len(R_reduced)))
    pos = {orig: j for j, orig in enumerate(R)}
    idx = [pos[a] for a in R_reduced]
    D_all_new = D_all[np.ix_(idx, idx)] if idx else np.zeros((0, 0), dtype=float)

    # ==================================================
    # B) Reduce inner_models (Type 2)
    # ==================================================
    updated_models: List[Dict] = []
    removed_outer_locals: Set[int] = set()
    for model in inner_models:
        oi_global = int(model["outer_index_global"])
        route_nodes_global_old: List[int] = list(model["route_nodes_global"])
        oi_local_old = int(model["outer_index"])
        route_nodes_local_old: List[int] = list(model["route_nodes"])
        kept_route_nodes_global = [
            a for a in route_nodes_global_old if a not in S
        ]
        if len(kept_route_nodes_global) == 0:
            removed_outer_locals.add(oi_local_old)
            continue
        D_inner_old = np.asarray(model["D_inner"], dtype=float)
        k_old = len(route_nodes_local_old)
        if D_inner_old.shape != (k_old + 2, k_old + 2):
            raise ValueError(
                f"Unit outer_index_global={oi_global}: "
                f"inconsistent D_inner shape {D_inner_old.shape}, "
                f"expected {(k_old+2, k_old+2)}."
            )
        keep_local_addr_idx = [
            i + 1
            for i, a in enumerate(route_nodes_global_old)
            if a not in S
        ]
        keep_local_idx = [0] + keep_local_addr_idx + [k_old + 1]
        D_inner_new = D_inner_old[np.ix_(keep_local_idx, keep_local_idx)]
        route_nodes_local_new: List[int] = []
        for a in kept_route_nodes_global:
            if a not in address_index_map:
                raise ValueError(
                    f"Address {a} kept in unit {oi_global} "
                    f"but not present in reduced R."
                )
            route_nodes_local_new.append(address_index_map[a])
        node_map_new = {
            i + 1: addr_local
            for i, addr_local in enumerate(route_nodes_local_new)
        }
        new_model = dict(model)
        new_model["route_nodes"] = route_nodes_local_new
        new_model["node_map"] = node_map_new
        new_model["D_inner"] = D_inner_new
        new_model["entry_index"] = 0
        new_model["exit_index"] = len(route_nodes_local_new) + 1
        new_model["route_nodes_global"] = kept_route_nodes_global
        new_model["outer_index_global"] = oi_global
        updated_models.append(new_model)

    # ==================================================
    # C) Reduce outer graph if entire units removed
    # ==================================================
    if len(updated_models) == 0:
        return (
            np.zeros((0, 0), dtype=float),
            D_all_new,
            R_local_reduced,
            [],
            {},
            address_index_map,
        )
    if not removed_outer_locals:
        outer_index_map = {
            int(m["outer_index"]): int(m["outer_index"])
            for m in updated_models
        }
        return (
            D_outer,
            D_all_new,
            R_local_reduced,
            updated_models,
            outer_index_map,
            address_index_map,
        )
    kept_outer_locals = sorted({int(m["outer_index"]) for m in updated_models})
    outer_index_map = {
        old_local: new_local
        for new_local, old_local in enumerate(kept_outer_locals)
    }
    D_outer_new = D_outer[np.ix_(kept_outer_locals, kept_outer_locals)]
    for m in updated_models:
        old_local = int(m["outer_index"])
        m["outer_index"] = outer_index_map[old_local]
    updated_models.sort(key=lambda mm: int(mm["outer_index"]))
    return (
        D_outer_new,
        D_all_new,
        R_local_reduced,
        updated_models,
        outer_index_map,
        address_index_map,
    )

def _solve_outer_structured(
    D_outer: np.ndarray,
    inner_models: List[Dict],
    outer_cache: Dict,
    *,
    problem_type: STRUCTURED_PROBLEM_TYPES = "OUT:TSP",
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    ortools_time_limit: int = 2,
    fixed_endpoints=None,
    initial_point_method: Dict | None = None,
    ) -> Tuple[List[int], float, Dict]:
    """
    Solve outer structured routing.

    -------
    Returns
    -------
    outer_order_local : Order of LOCAL outer indices for this call.
    L_outer : Outer route length.
    outer_cache : Updated outer cache (keys in GLOBAL unit identity space).
    """
    n_outer = len(inner_models)
    if n_outer == 0:
        return [], 0.0, outer_cache
    outer_local_to_global = {
        m["outer_index"]: m["outer_index_global"]
        for m in inner_models
    }
    outer_global_to_local = {
        m["outer_index_global"]: m["outer_index"]
        for m in inner_models
    }
    outer_units_global = sorted(outer_global_to_local.keys())
    outer_key = tuple(outer_units_global)
    if outer_key in outer_cache:
        outer_order_global, L_outer = outer_cache[outer_key]
        outer_order_local = [
            outer_global_to_local[g] for g in outer_order_global
        ]
        return outer_order_local, L_outer, outer_cache
    if problem_type == "OUT:TSP":
        outer_order_local, L_outer = tsp_solve(
            D_outer,
            deterministic_tsp=deterministic,
            solver=solver,
            ortools_time_limit=ortools_time_limit,
        )
    elif problem_type == "OUT:HPP":
        outer_order_local, L_outer = hpp_solve(
            D_outer,
            solver=solver,
            fixed_endpoints=fixed_endpoints,
            initial_point_method=initial_point_method,
            ortools_time_limit=ortools_time_limit,
            deterministic=deterministic,
        )
    else:
        raise ValueError(f"Unknown problem_type: {problem_type}")
    outer_order_global = [
        outer_local_to_global[i] for i in outer_order_local
    ]
    outer_cache[outer_key] = (outer_order_global, float(L_outer))
    return outer_order_local, float(L_outer), outer_cache

def _solve_inner_structured(
    outer_order_local: List[int],
    inner_models: List[Dict],
    inner_cache: Dict,
    *,
    deterministic: bool = True,
    solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int = 2,
    ) -> Tuple[List[int], float, Dict]:
    """
    Solve inner HPP routes per unit.
    -------
    Returns
    -------
    R_seq_local : Concatenated LOCAL address sequence.
    L_inner_total : Sum of inner route lengths.
    inner_cache : Updated inner cache (keys in GLOBAL identity space).
    """
    inner_by_outer = {m["outer_index"]: m for m in inner_models}
    R_seq_local: List[int] = []
    L_inner_total = 0.0
    for oi_local in outer_order_local:
        model = inner_by_outer[oi_local]
        oi_global = model["outer_index_global"]
        route_nodes_local = model["route_nodes"]
        route_nodes_global = model["route_nodes_global"]
        addr_global_to_local = {
            g: l for g, l in zip(route_nodes_global, route_nodes_local)
        }
        D_inner = model["D_inner"]
        entry = model["entry_index"]
        exit_ = model["exit_index"]
        node_map_local = model.get("node_map")
        if node_map_local is None:
            node_map_local = {
                i + 1: route_nodes_local[i]
                for i in range(len(route_nodes_local))
            }
        node_map_global = model.get("node_map_global")
        if node_map_global is None:
            node_map_global = {
                i + 1: route_nodes_global[i]
                for i in range(len(route_nodes_global))
            }
        inner_key = (oi_global, tuple(route_nodes_global))
        if inner_key in inner_cache:
            inner_route_global, L_inner = inner_cache[inner_key]
            inner_route_local = [
                addr_global_to_local[g] for g in inner_route_global
            ]
        else:
            order_local, L_inner = hpp_solve(
                D_inner,
                solver=solver,
                fixed_endpoints={"start": entry, "end": exit_},
                ortools_time_limit=ortools_time_limit,
                deterministic=deterministic,
            )
            inner_route_global = [
                node_map_global[i]
                for i in order_local
                if i not in (entry, exit_)
            ]
            inner_route_local = [
                node_map_local[i]
                for i in order_local
                if i not in (entry, exit_)
            ]
            inner_cache[inner_key] = (inner_route_global, float(L_inner))
        R_seq_local.extend(inner_route_local)
        L_inner_total += float(L_inner)
    return R_seq_local, float(L_inner_total), inner_cache

def solve_structured_route(
    D_outer: np.ndarray,
    D_all: np.ndarray,
    R: List[int],
    inner_models: List[Dict],
    strict_order: bool,
    problem_type: STRUCTURED_PROBLEM_TYPES,
    *,
    L_u: float | List[float] | np.ndarray = 0.0,
    deterministic: bool = True,
    solver: SOLVERS = "ortools",
    inner_solver: HPP_SOLVERS = "ortools",
    ortools_time_limit: int = 2,
    fixed_endpoints=None,
    initial_point_method: Dict | None = None,
    inner_cache: Optional[Dict] = None,
    outer_cache: Optional[Dict] = None,
    ) -> Tuple[List[int], float, Dict, Dict]:
    """
    Solve a single structured route.

    Type 1 (strict_order=True):
        Evaluate a fixed address order R on D_all (no optimization).
    Type 2 (strict_order=False):
        Optimize unit order on D_outer (TSP/HPP) and optimize traversal inside each unit (HPP).

    Parameters
    ----------
    D_outer : Unit-to-unit distance matrix (exit -> entry), Type 2 only.
    D_all : Address-to-address distance matrix, Type 1 only.
    R : Fixed address order (global route_numbers), Type 1 only.
    inner_models : Structured unit descriptions, Type 2 only.
    problem_type : "OUT:TSP" or "OUT:HPP".
    strict_order : Select Type 1 (True) or Type 2 (False).
    inner_cache : Cache for inner HPP solutions (GLOBAL keys).
    outer_cache : Cache for outer TSP/HPP solutions (GLOBAL keys).

    Returns
    -------
    R_seq : Local address order for this solve.
    L : Total route length.
    inner_cache : Updated inner cache.
    outer_cache : Updated outer cache.
    """
    # --------------------------------------------------
    # TYPE 1: fixed order, no optimization
    # --------------------------------------------------
    if strict_order:
        if problem_type == "OUT:TSP":
            base_problem_type = "TSP"
        elif problem_type == "OUT:HPP":
            base_problem_type = "HPP"
        else:
            raise ValueError(f"Unknown problem_type: {problem_type}")
        R_seq = list(R)
        L = route_length_type1(
            D_all,
            R_seq,
            L_u=L_u,
            problem_type=base_problem_type,
        )
        return R_seq, float(L), {}, {}
    # --------------------------------------------------
    # TYPE 2: structured optimization
    # --------------------------------------------------
    if inner_cache is None:
        inner_cache = {}
    if outer_cache is None:
        outer_cache = {}
    outer_order_local, L_outer, outer_cache = _solve_outer_structured(
        D_outer=D_outer,
        inner_models=inner_models,
        problem_type=problem_type,
        deterministic=deterministic,
        solver=solver,
        ortools_time_limit=ortools_time_limit,
        fixed_endpoints=fixed_endpoints,
        initial_point_method=initial_point_method,
        outer_cache=outer_cache,
    )
    R_seq_local, L_inner_total, inner_cache = _solve_inner_structured(
        outer_order_local=outer_order_local,
        inner_models=inner_models,
        deterministic=deterministic,
        solver=inner_solver,
        ortools_time_limit=ortools_time_limit,
        inner_cache=inner_cache,
    )
    L_total = float(L_outer) + float(L_inner_total)
    return R_seq_local, L_total, inner_cache, outer_cache