# libraries

This folder contains the complete implementation of the outlier detection
and route optimization framework.

The `libraries` package is structured to clearly separate:
- core algorithmic logic
- data preprocessing and routing utilities
- experimental and validation code
- execution entry points
- visualization and presentation components

All functionality used by applications, simulations, and runners
is organized within this folder.

## Structure
```
libraries/
├── utils/         # Core utilities, algorithms, pipelines, and visualization
├── classes/       # Higher-level class abstractions (GeoJSON, OSRM, plotting)
├── runners/       # Runtime-driven execution entry points for pipelines
├── simulations/   # Benchmarks, validation, and experimental scripts
└── tests/         # Automated test suite (pytest-based)
```
Each subfolder has its own README file describing responsibilities
and internal structure.

## Module usage

The overall dependency structure is layered:

- `utils` provides the foundational building blocks
- `classes` wrap selected utilities into higher-level abstractions
- `pipelines` (inside `utils`) orchestrate data flow and computation
- `runners` act as thin entry points driven by runtime configuration
- `simulations` and `tests` use the above components for validation,
  benchmarking, and experimentation

Algorithmic logic is intentionally isolated from:
- execution context
- configuration
- visualization

This separation ensures that algorithms can be reused consistently
across different applications and analysis workflows.

## Design principles

The codebase follows these principles:

- clear separation of concerns
- reuse of algorithmic components across contexts
- configuration-driven execution
- minimal coupling between computation and presentation

The structure is intentionally open-ended, allowing new modules,
experiments, and applications to be added without restructuring
existing components.