import numpy as np
from libraries.utils.algorithm.solvers.common import _to_pylist
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from tqdm import tqdm
from libraries.utils.algorithm.solvers.greedy import greedy_hpp_denn,greedy_hpp_algorithm


def furthest_away_greedy(D: np.ndarray,
                        n_edges: int,
                        start_fixed: int | None = None,
                        end_fixed: int | None = None,
                        k_candidates: int = 10):
    n = len(D)
    if n_edges >= n:
        raise ValueError(f"n_edges must be < number of nodes (n={n}), got n_edges={n_edges}.")
    nearest = np.argsort(D, axis=1)
    best_len = -np.inf
    best_pair = None
    for i in range(n):
        if start_fixed is not None and i != start_fixed:
            continue
        for j in range(n):
            if i == j:
                continue
            if end_fixed is not None and j != end_fixed:
                continue
            visited = {i}
            current = i
            length = 0.0
            valid = True
            for _ in range(n_edges - 1):
                candidates = [
                    v for v in nearest[current][:k_candidates]
                    if v not in visited and v != j
                ]
                if not candidates:
                    valid = False
                    break
                next_node = candidates[0]
                length += D[current, next_node]
                visited.add(next_node)
                current = next_node
            if not valid or j in visited:
                continue
            length += D[current, j]
            if length > best_len:
                best_len = length
                best_pair = (i, j)
    return best_pair, best_len

def _solve_fixed_hpp_ortools(
    D: np.ndarray,
    start: int,
    end: int,
    ortools_time_limit: int = 5,
    deterministic: bool = True,
    ) -> tuple[list[int], float]:
    """
    Solve a fixed-start, fixed-end Hamiltonian Path Problem (HPP)
    using OR-Tools.

    Parameters
    ----------
    deterministic : bool (default=True)
        If True:
            - Use GREEDY_DESCENT
            - Stop early via solution_limit
        If False:
            - Use GUIDED_LOCAL_SEARCH
            - Run until time_limit
    """
    n = len(D)
    manager = pywrapcp.RoutingIndexManager(
        n,
        1,
        [start],
        [end],
    )
    routing = pywrapcp.RoutingModel(manager)
    dist = lambda i, j: int(D[manager.IndexToNode(i), manager.IndexToNode(j)] * 10000)
    transit_index = routing.RegisterTransitCallback(dist)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    if deterministic:
        params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT
        )
        params.time_limit.FromSeconds(ortools_time_limit)
        params.solution_limit = n
    else:
        params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        params.time_limit.FromSeconds(ortools_time_limit)
    solution = routing.SolveWithParameters(params)
    if solution is None:
        raise RuntimeError("OR-Tools failed to find a solution.")
    idx = routing.Start(0)
    path = []
    while not routing.IsEnd(idx):
        path.append(manager.IndexToNode(idx))
        idx = solution.Value(routing.NextVar(idx))
    path.append(end)
    L = sum(D[path[i], path[i + 1]] for i in range(len(path) - 1))
    return _to_pylist(path), float(L)

def _hpp_ortools(
    D: np.ndarray,
    fixed_endpoints: dict | None,
    initial_point_method: dict = {"method": "GREEDY_DNN"},
    ortools_time_limit: int = 2,
    deterministic: bool = True
    ) -> tuple[list[int], float]:
    """
    OR-Tools-based HPP solver with optional endpoint candidate generation.

    If both start and end are fixed, the function directly solves the fixed
    HPP instance using OR-Tools. Otherwise, candidate start/end pairs are
    generated according to the specified initial_point_method and evaluated
    using OR-Tools.
    """
    n = len(D)
    fixed_endpoints = fixed_endpoints or {"start": None, "end": None}
    start_fixed = fixed_endpoints.get("start")
    end_fixed = fixed_endpoints.get("end")
    # --------------------------------------------------
    # FAST PATH: both endpoints are fixed
    # --------------------------------------------------
    if start_fixed is not None and end_fixed is not None:
        return _solve_fixed_hpp_ortools(
            D,
            start_fixed,
            end_fixed,
            ortools_time_limit,
        )
    # --------------------------------------------------
    # INDEX: fixed deterministic endpoints (0 -> n-1)
    # --------------------------------------------------
    method = initial_point_method.get("method")
    if method == "INDEX":
        return _solve_fixed_hpp_ortools(
            D,
            start=0,
            end=n - 1,
            ortools_time_limit=ortools_time_limit,
            deterministic=deterministic
        )
    # --------------------------------------------------
    # EXTENDED_SEARCH: multiple OR-Tools runs
    # --------------------------------------------------
    if method == "EXTENDED_SEARCH":
        n_iter = min(initial_point_method.get("n_iterations", 1), n)
        node_scores = [
            (np.sum(D[i, :]) + np.sum(D[:, i]), i)
            for i in range(n)
        ]
        node_scores.sort(reverse=True)
        best_route = None
        best_len = np.inf
        ortools_time_limit_extended = initial_point_method.get("time_limit", ortools_time_limit)
        for _, anchor in tqdm(node_scores[:n_iter],desc="Extended search: ", leave=False):
            if start_fixed is not None:
                s = start_fixed
                e_candidates = [anchor]
            elif end_fixed is not None:
                s = anchor
                e_candidates = [end_fixed]
            else:
                s = anchor
                e_candidates = [j for j in range(n) if j != s]
            for e in tqdm(e_candidates,desc=f"Extended search for start={anchor}: ", leave=False):
                if s == e:
                    continue
                try:
                    route, L = _solve_fixed_hpp_ortools(D, s, e, ortools_time_limit_extended,deterministic=deterministic)
                except RuntimeError:
                    continue
                if L < best_len:
                    best_len = L
                    best_route = route
        if best_route is None:
            raise RuntimeError("EXTENDED_SEARCH failed to find any valid route.")
        return best_route, best_len
    # --------------------------------------------------
    # GREEDY: SIMPLY ONEWAY GREEDY endpoint selection
    # --------------------------------------------------
    elif method == "GREEDY":
        path, _ = greedy_hpp_algorithm(D, fixed_endpoints)
        s, e = path[0], path[-1]
        return _solve_fixed_hpp_ortools(D,s,e,ortools_time_limit,deterministic=deterministic)
    # --------------------------------------------------
    # GREEDY_DNN: DENN-based endpoint selection
    # --------------------------------------------------
    elif method == "GREEDY_DNN":
        path, _ = greedy_hpp_denn(D, fixed_endpoints)
        s, e = path[0], path[-1]
        return _solve_fixed_hpp_ortools(D,s,e,ortools_time_limit,deterministic=deterministic)
    # --------------------------------------------------
    # FURTHEST_AWAY: greedy distance-maximizing endpoints
    # --------------------------------------------------
    elif method == "FURTHEST_AWAY":
        n_edges = int(initial_point_method.get("n_edges", 1))
        (s, e), _ = furthest_away_greedy(D,n_edges=n_edges,start_fixed=start_fixed, end_fixed=end_fixed)
        return _solve_fixed_hpp_ortools(D,s,e,ortools_time_limit,deterministic=deterministic)
    else:
        raise ValueError(f"Unknown initial_point_method: {method}")