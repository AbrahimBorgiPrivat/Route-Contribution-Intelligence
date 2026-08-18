# utils

This folder contains shared utility modules used across the entire project.

The utilities here provide common building blocks that support algorithms,
pipelines, simulations, runtime configuration, and visualization.

The folder is organized by responsibility to ensure reuse and clear separation
between computation, orchestration, and presentation.

## Structure
```
utils/
├── algorithm/          # Core algorithmic logic (Type 1 / 2 / 3)
├── experiments/        # Helpers for simulations and experiments
├── pipelines/          # Orchestration of data flow and execution
├── preprocessing/      # Data preparation and normalization
├── runtime/            # Runtime configuration and parameter loading
└── visualization/      # GeoJSON, maps, and HTML generation
```
## Module usage

All submodules in this folder are designed to be reused across the codebase.
Higher-level components (pipelines, simulations, applications) depend on
these utilities, while utilities themselves remain free of application logic.
