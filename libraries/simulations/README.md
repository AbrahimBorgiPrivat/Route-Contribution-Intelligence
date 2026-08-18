# simulations

This folder contains scripts and data used for experiments, benchmarks,
and validation of the algorithms implemented in the project.

The simulations layer is responsible for evaluating correctness,
robustness, and performance under controlled conditions.
It does not implement new algorithmic logic, but orchestrates and
analyzes existing components.

## Structure

```
simulations/
├── benchmarks/    # Performance and scalability benchmarks
├── validation/    # Correctness and robustness validation
├── _data/         # Input data used by simulations
└── _img/          # Generated figures and plots
```

Additional simulation categories may be added as the project evolves.

## Module usage

Simulation scripts typically import utilities, algorithms, and pipelines
from `libraries.utils` and are executed in batch mode to generate results
used in analysis and reporting.
