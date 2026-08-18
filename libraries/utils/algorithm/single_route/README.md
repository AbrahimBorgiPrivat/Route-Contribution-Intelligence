# single_route

This folder contains algorithms and helper functions for outlier detection
on a single route.

The focus here is on:
- marginal effect computation
- Type 1 and Type 2 logic for a single route
- route cost and coverage calculations
- assembling algorithmic steps into a coherent workflow

These components form the basis for both direct analysis
and reuse in hybrid and Type 3 methods.

## Structure

```
single_route/
├── core_algorithm.py      # Combines the other modules to run Type 1 / Type 2 outlier detection
├── coverage_cost.py       # Computes marginal gains and ΔMG / coverage effects
├── outlier_detection.py   # Selects candidate outliers based on criteria such as C₂(S) > z
├── route_costs.py         # Computes cost impact of removing candidate sets S
└── route_solver.py        # Computes paths through D after removal of candidates
```

## Module usage

The modules in this folder are designed to be composed into a single
outlier-detection workflow, with `core_algorithm.py` acting as the central
orchestrator.

Conceptually, the data flow is:

solvers → route_solver.py → route_costs.py → core_algorithm.py  
solvers → route_solver.py → core_algorithm.py  
structural_heuristics → core_algorithm.py  
outlier_detection.py → core_algorithm.py  
coverage_cost.py → core_algorithm.py

This structure allows the same logic to be reused across single-route analysis,
hybrid methods, and the multi-route Type 3 framework.
