import numpy as np
from typing import List, Tuple, Dict, Optional
from libraries.utils.algorithm.solvers.common import _to_pylist

def greedy_tsp_algorithm(D: np.ndarray) -> tuple[list[int], float]:
    """
    Fully deterministic greedy TSP heuristic.
    For every possible start node:
        - Grow a route by repeatedly selecting the nearest unvisited node.
        - Compute its total tour length.
    Returns the best greedy tour among all starting nodes.
    ----------
    Parameters
    ----------
    Dmat : Distance Matrice.
    
    ----------
    Returns
    ----------
    route_order : Visiting order for the TSP tour
    """
    n = len(D)
    def greedy_from(start):
        visited = {start}
        order = [start]
        while len(visited) < n:
            last = order[-1]
            next_node = np.argmin([
                D[last, j] if j not in visited else np.inf
                for j in range(n)
            ])
            order.append(next_node)
            visited.add(next_node)
        return order
    best_order = None
    best_len = np.inf
    for s in range(n):
        route = greedy_from(s)
        L = sum(D[route[i], route[(i + 1) % n]] for i in range(n))
        if L < best_len:
            best_len = L
            best_order = route
    return _to_pylist(best_order), best_len

def greedy_hpp_algorithm(
    D: np.ndarray,
    fixed_endpoints: Optional[Dict[str, int | None]] = None,
    ) -> Tuple[List[int], float]:
    """
    Fully deterministic greedy HPP heuristic (multi-start nearest neighbor),
    with optional fixed start and/or end node.
    ----------
    D : Asymmetric distance matrix.
    fixed_endpoints : {"start": int | None, "end": int | None}
    Returns
    route_order : Visiting order for the HPP path (open route).
    L_opt : Total path length (no return edge).
    """
    n = len(D)
    if fixed_endpoints is None:
        fixed_endpoints = {"start": None, "end": None}
    start_fixed = fixed_endpoints.get("start")
    end_fixed = fixed_endpoints.get("end")
    if start_fixed is not None and end_fixed is not None and start_fixed == end_fixed:
        raise ValueError("Fixed start and end cannot be the same node for HPP.")
    def greedy_from(start: int) -> Tuple[List[int], float]:
        visited = {start}
        path = [start]
        total_length = 0.0
        forbidden = {end_fixed} if end_fixed is not None else set()
        while len(visited) < n - (1 if end_fixed is not None else 0):
            last = path[-1]
            next_node = min(
                (j for j in range(n) if j not in visited and j not in forbidden),
                key=lambda j: D[last, j],
            )
            total_length += D[last, next_node]
            path.append(next_node)
            visited.add(next_node)
        if end_fixed is not None:
            total_length += D[path[-1], end_fixed]
            path.append(end_fixed)
        return path, total_length
    # --------------------------------------------------
    # Determine start candidates
    # --------------------------------------------------
    if start_fixed is not None:
        start_nodes = [start_fixed]
    else:
        start_nodes = [i for i in range(n) if i != end_fixed]
    best_path = None
    best_len = np.inf
    for s in start_nodes:
        path, L = greedy_from(s)
        if L < best_len:
            best_len = L
            best_path = path
    return best_path, float(best_len)

def greedy_hpp_denn(
    D: np.ndarray,
    fixed_endpoints: dict | None = None,
    ) -> Tuple[List[int], float]:
    """
    Fully deterministic greedy TSP heuristic.
    ----------
    Dmat : Distance Matrice.
    ----------
    Returns
    route_order : Visiting order for the TSP tour
    """
    n = len(D)
    if fixed_endpoints is None:
        fixed_endpoints = {"start": None, "end": None}
    start_fixed = fixed_endpoints.get("start")
    end_fixed = fixed_endpoints.get("end")
    if start_fixed is not None and end_fixed is not None and start_fixed == end_fixed:
        raise ValueError("Fixed start and end cannot be the same node.")

    def initial_paths():
        """
        Generate initial seed paths depending on fixed start/end constraints.
        - Fixed start and end: initialize path anchored at both endpoints.
        - Fixed start only   : initialize path starting at start_fixed.
        - Fixed end only     : initialize path ending at end_fixed.
        - No constraints     : try all nodes as starting points.
        """
        if start_fixed is not None and end_fixed is not None:
            return [[start_fixed, end_fixed]]
        elif start_fixed is not None:
            return [[start_fixed]]
        elif end_fixed is not None:
            return [[end_fixed]]
        else:
            return [[i] for i in range(n)]

    def denn_from(path: List[int]) -> List[int]:
        """
        Expand a partial path into a full Hamiltonian path using
        the Double-Ended Nearest Neighbor (DENN) heuristic.
        """
        visited = set(path)
        while len(visited) < n:
            left = path[0]
            right = path[-1]
            best_node = None
            best_cost = np.inf
            attach_left = False
            insert_pos = None
            both_fixed = (
                start_fixed is not None
                and end_fixed is not None
                and left == start_fixed
                and right == end_fixed
            )
            for j in range(n):
                if j in visited:
                    continue
                if both_fixed:
                    for i in range(len(path) - 1):
                        cost = D[path[i], j] + D[j, path[i + 1]] - D[path[i], path[i + 1]]
                        if cost < best_cost:
                            best_cost = cost
                            best_node = j
                            insert_pos = i + 1
                else:
                    if start_fixed is None or left != start_fixed:
                        cost_left = D[j, left]
                        if cost_left < best_cost:
                            best_cost = cost_left
                            best_node = j
                            attach_left = True
                            insert_pos = None
                    if end_fixed is None or right != end_fixed:
                        cost_right = D[right, j]
                        if cost_right < best_cost:
                            best_cost = cost_right
                            best_node = j
                            attach_left = False
                            insert_pos = None
            if best_node is None:
                raise RuntimeError("No valid attachment found (check endpoint constraints).")
            if both_fixed:
                path.insert(insert_pos, best_node)
            else:
                if attach_left:
                    path.insert(0, best_node)
                else:
                    path.append(best_node)
            visited.add(best_node)
        return path
    best_path = None
    best_len = np.inf
    for seed in initial_paths():
        path = denn_from(seed.copy())
        L = sum(D[path[i], path[i + 1]] for i in range(n - 1))
        if L < best_len:
            best_len = L
            best_path = path
    return _to_pylist(best_path), float(best_len)

def greedy_hpp_cheapest_insertion(
    D: np.ndarray,
    fixed_endpoints: Optional[Dict[str, int | None]] = None,
    ) -> Tuple[List[int], float]:
    """
    Fully deterministic Cheapest Insertion heuristic for the Hamiltonian Path Problem (HPP).
    Builds an open path through all nodes by repeatedly inserting the node that yields the
    smallest increase in path length.
    ----------
    D : np.ndarray
        Asymmetric distance matrix, shape (n, n).
    fixed_endpoints : dict | None
        {"start": int | None, "end": int | None}
    -------
    Returns
    path : List[int]
        Visiting order for the HPP path (open route).
    length : float
        Total path length (no return edge).
    """
    D = np.asarray(D, dtype=float)
    n = D.shape[0]
    if D.shape[0] != D.shape[1]:
        raise ValueError("D must be a square matrix.")

    fixed_endpoints = fixed_endpoints or {"start": None, "end": None}
    start_fixed = fixed_endpoints.get("start")
    end_fixed = fixed_endpoints.get("end")

    if start_fixed is not None and (start_fixed < 0 or start_fixed >= n):
        raise ValueError("fixed start is out of bounds.")
    if end_fixed is not None and (end_fixed < 0 or end_fixed >= n):
        raise ValueError("fixed end is out of bounds.")
    if start_fixed is not None and end_fixed is not None and start_fixed == end_fixed and n > 1:
        raise ValueError("Fixed start and end cannot be the same node when n > 1.")

    def _path_length(path: List[int]) -> float:
        if len(path) <= 1:
            return 0.0
        return float(sum(D[path[i], path[i + 1]] for i in range(len(path) - 1)))

    def _best_seed_for_fixed_start(s: int) -> List[int]:
        if n == 1:
            return [s]
        candidates = [j for j in range(n) if j != s and (end_fixed is None or j != end_fixed)]
        if not candidates:
            # Only possible when n==2 and end_fixed==the other node, handled elsewhere.
            candidates = [j for j in range(n) if j != s]
        j_best = min(candidates, key=lambda j: (D[s, j], j))
        return [s, j_best]

    def _best_seed_for_fixed_end(e: int) -> List[int]:
        if n == 1:
            return [e]
        candidates = [i for i in range(n) if i != e and (start_fixed is None or i != start_fixed)]
        if not candidates:
            candidates = [i for i in range(n) if i != e]
        i_best = min(candidates, key=lambda i: (D[i, e], i))
        return [i_best, e]

    def _solve_from_seed(seed: List[int]) -> Tuple[List[int], float]:
        path = seed[:]
        visited = set(path)
        if start_fixed is not None and path[0] != start_fixed:
            raise RuntimeError("Seed does not respect fixed start.")
        if end_fixed is not None and path[-1] != end_fixed:
            raise RuntimeError("Seed does not respect fixed end.")
        can_extend_left = (start_fixed is None)
        can_extend_right = (end_fixed is None)
        while len(visited) < n:
            best_delta = np.inf
            best_node = None
            best_mode = None  
            best_pos = None   
            for node in range(n):
                if node in visited:
                    continue
                if can_extend_left:
                    delta = D[node, path[0]]
                    key = (delta, node, -1)  
                    if key < (best_delta, best_node if best_node is not None else np.inf, best_pos if best_pos is not None else np.inf):
                        best_delta, best_node, best_mode, best_pos = delta, node, "left", -1
                if can_extend_right:
                    delta = D[path[-1], node]
                    key = (delta, node, 10**9)
                    if key < (best_delta, best_node if best_node is not None else np.inf, best_pos if best_pos is not None else np.inf):
                        best_delta, best_node, best_mode, best_pos = delta, node, "right", 10**9
                for i in range(len(path) - 1):
                    a = path[i]
                    b = path[i + 1]
                    delta = D[a, node] + D[node, b] - D[a, b]
                    key = (delta, node, i + 1)
                    cur = (best_delta, best_node if best_node is not None else np.inf, best_pos if best_pos is not None else np.inf)
                    if key < cur:
                        best_delta, best_node, best_mode, best_pos = delta, node, "between", i + 1
            if best_node is None:
                raise RuntimeError("No feasible insertion found (endpoint constraints too restrictive).")
            if best_mode == "left":
                path.insert(0, best_node)
            elif best_mode == "right":
                path.append(best_node)
            else:  
                path.insert(best_pos, best_node)
            visited.add(best_node)
        if start_fixed is not None and path[0] != start_fixed:
            raise RuntimeError("Final path violates fixed start.")
        if end_fixed is not None and path[-1] != end_fixed:
            raise RuntimeError("Final path violates fixed end.")
        if sorted(path) != list(range(n)):
            raise RuntimeError("Final path is not a permutation of nodes.")
        return path, _path_length(path)
    # ---------------------------
    # Seed selection (deterministic)
    # ---------------------------
    if n == 0:
        return [], 0.0
    if n == 1:
        return [0], 0.0
    if start_fixed is not None and end_fixed is not None:
        seed = [start_fixed, end_fixed] if start_fixed != end_fixed else [start_fixed]
        return _solve_from_seed(seed)
    if start_fixed is not None:
        seed = _best_seed_for_fixed_start(start_fixed)
        return _solve_from_seed(seed)
    if end_fixed is not None:
        seed = _best_seed_for_fixed_end(end_fixed)
        return _solve_from_seed(seed)
    best_path = None
    best_len = np.inf
    for s in range(n):
        seed = _best_seed_for_fixed_start(s)  
        path, L = _solve_from_seed(seed)
        if L < best_len:
            best_len = L
            best_path = path
    return best_path, float(best_len)