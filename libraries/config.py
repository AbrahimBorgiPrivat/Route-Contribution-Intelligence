from typing import Literal,Union

HIGHWAY_TYPES = Literal[
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "service",
    "living_street",
]
# HYBRID METHODS
HYBRID_METHODS = Literal["A", "B", "Beam", "U"]
HYBRID_METHODS_LIST = ["A", "B", "Beam", "U"]
# PROBLEM TYPES
STRUCTURED_PROBLEM_TYPES = Literal[ "OUT:TSP", "OUT:HPP"]
UNSTRUCTURED_PROBLEM_TYPES = Literal["TSP", "HPP"]
PROBLEM_TYPES = Union[STRUCTURED_PROBLEM_TYPES, UNSTRUCTURED_PROBLEM_TYPES]

STRUCTURED_PROBLEM_TYPES_SET = {"OUT:TSP", "OUT:HPP"}
UNSTRUCTURED_PROBLEM_TYPES_SET = {"TSP", "HPP"}
PROBLEM_TYPES_SET = STRUCTURED_PROBLEM_TYPES_SET | UNSTRUCTURED_PROBLEM_TYPES_SET

# SOLVERS
HPP_SOLVERS = Literal["greedy","greedy_denn", "cheapest_insertion", "ortools", "exact"]
TSP_SOLVERS = Literal["greedy", "python_tsp", "ortools", "lkh", "exact"] 
SOLVERS = Union[HPP_SOLVERS, TSP_SOLVERS]

HPP_SOLVERS_SET = {"greedy","greedy_denn", "cheapest_insertion", "ortools", "exact"}
TSP_SOLVERS_SET = {"greedy", "python_tsp", "ortools", "lkh", "exact"}
SOLVERS_SET = HPP_SOLVERS_SET | TSP_SOLVERS_SET