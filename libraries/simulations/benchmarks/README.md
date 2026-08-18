# benchmarks

This folder contains benchmark scripts used to evaluate the performance
and scalability of routing and outlier detection algorithms.

Benchmarks focus on runtime, solution quality, and solver behavior
as problem size increases.

## Structure

```
benchmarks/
├── tsp/      # Benchmarks for TSP-based solvers
├── hpp/      # Benchmarks for HPP-based solvers
├── hybrid/   # Benchmarks for hybrid and candidate-based methods
└── ...
```

Each subfolder groups benchmark scripts by problem type.

## Module usage

Benchmark scripts invoke solvers and algorithms through the utility layer
and record performance metrics for later analysis and visualization.
