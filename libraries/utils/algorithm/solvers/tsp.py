import elkai
import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from python_tsp.heuristics import solve_tsp_local_search
from typing import Literal

from libraries.utils.algorithm.solvers.common import _to_pylist
from libraries.utils.algorithm.solvers.greedy import greedy_tsp_algorithm
from libraries.utils.algorithm.solvers.exact_solvers import exact_tsp_held_karp
from libraries.config import TSP_SOLVERS

def tsp_solve(D: np.ndarray,
              deterministic_tsp: bool = True,
              solver: TSP_SOLVERS = "ortools",
              ortools_time_limit: int = 5,
              lkh_scale: int = 100
              ) -> tuple[list[int], float]:
    """
    Unified TSP solver with multiple backend options.
    ----------
    Parameters
    ----------
    deterministic_tsp :
        - For "greedy": Fully deterministic nearest-neighbor multi-start heuristic.
        - For "python_tsp":Use deterministic greedy initialization, BUT the python_tsp local search itself remains stochastic.
        - For "ortools": Use GREEDY_DESCENT (when deterministic_tsp is true) with small time and solution limits. This produces *mostly deterministic* results but not guaranteed.
        - "lkh"         : uses LKH in ATSP-mode. 
    solver:
        "greedy"      => deterministic O(n^2) nearest-neighbor heuristic
        "python_tsp"  => heuristic, fast, stochastic
        "ortools"     => high-quality, mostly deterministic when deterministic_tsp=True
        "lkh"         => LKH solver (state-of-the-art heuristic TSP engine), ATSP mode
        "exact"       => Exact Held–Karp DP (REFERENCE ONLY).
                         Exponential time O(n^2·2^n).
                         Not suitable for production use.
    
    -------
    Returns
    -------
    route_order : Visiting order for the TSP tour
    L_opt : Total tour length using matrix D
    """
    n = len(D)
    if solver == "python_tsp":
        if deterministic_tsp:
            best_x0, _ = greedy_tsp_algorithm(D)
            route_order, L_opt = solve_tsp_local_search(D, x0=best_x0)
            return _to_pylist(route_order), L_opt
        else:
            route_order, L_opt = solve_tsp_local_search(D)
            return _to_pylist(route_order), L_opt
    elif solver == "greedy":
        return greedy_tsp_algorithm(D)
    elif solver == "ortools":
        manager = pywrapcp.RoutingIndexManager(n, 1, [0], [0])
        routing = pywrapcp.RoutingModel(manager)
        dist = lambda i, j: int(D[manager.IndexToNode(i), manager.IndexToNode(j)] * 10000)
        transit_index = routing.RegisterTransitCallback(dist)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_index)
        params = pywrapcp.DefaultRoutingSearchParameters()
        params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        if deterministic_tsp:
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
            print("No solution found with OR-Tools; falling back to greedy algorithm.")
            return greedy_tsp_algorithm(D)
        idx = routing.Start(0)
        order = []
        while not routing.IsEnd(idx):
            order.append(manager.IndexToNode(idx))
            idx = solution.Value(routing.NextVar(idx))
        L = sum(D[order[i], order[(i + 1) % n]] for i in range(n))
        return _to_pylist(order), float(L)
    elif solver == "lkh":
        if n < 3:
            return greedy_tsp_algorithm(D)
        D_int = (D * lkh_scale).astype(int)
        dm = elkai.DistanceMatrix(D_int.tolist())
        route = dm.solve_tsp()
        route = route[:-1]
        L_opt = sum(D[route[i], route[(i+1) % n]] for i in range(n))
        return _to_pylist(route), float(L_opt)
    elif solver == "exact":
        return exact_tsp_held_karp(D)
    else:
        raise ValueError(f"Unknown solver: {solver}")