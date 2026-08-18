# solvers

This folder contains solver-specific implementations and shared solver abstractions.

The solvers are responsible for computing optimized route orderings and paths
used by Type 1, Type 2, and Type 3 algorithms.

## Structure

```
solvers/
├── common.py          # Shared solver utilities and abstractions
├── exact_solvers.py   # Exact solvers (used primarily for validation)
├── greedy.py          # Greedy and nearest-neighbor heuristics
├── hpp.py             # Solvers for open Hamiltonian Path Problems
├── ortools.py         # OR-Tools-based solvers
├── tsp.py             # Solvers for TSP variants
└── type1.py           # Solvers specific to fixed-order (Type 1) routes
```

## Module usage

Solver modules are called by higher-level route logic
(e.g. `route_solver.py`) and never directly by application code.

This separation allows solvers to be swapped or compared
without changing the surrounding algorithmic structure.
