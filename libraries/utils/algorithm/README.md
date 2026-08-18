# algorithm

This folder contains the core algorithmic components of the project.

It includes implementations related to:
- Type 1, Type 2, and Type 3 models
- outlier detection logic
- marginal cost and coverage calculations
- solver abstractions and heuristic strategies

The algorithm layer is structured to separate problem formulation,
solution methods, and search strategies.

## Structure

```
algorithm/
├── single_route/            # Algorithms for single-route problems (Type 1 / 2)
├── solvers/                 # Route solvers (exact and heuristic)
└── structural_heuristics/   # Heuristics for selecting outlier candidates
```

Additional algorithm modules may be added as new model variants or methods
are introduced.

## Module usage

The `algorithm` folder provides the computational core of the project.
Single-route logic is reused by hybrid and multi-route (Type 3) methods,
while solvers and heuristics are shared across multiple algorithm variants.
