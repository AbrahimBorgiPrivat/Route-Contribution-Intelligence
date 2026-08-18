# tests

This folder contains automated tests for the project, organized by module and functionality.

The test suite is designed to validate correctness, stability, and edge-case behavior
of the core algorithms, solvers, heuristics, and utility functions.

All tests follow standard `pytest` conventions and can be executed collectively
using pytest without additional configuration.

## Structure

```
tests/
├── beam_method/                 # Tests for beam-based structural heuristics
├── common/                      # Tests for shared helper functions
├── core_algorithm/              # Tests for core outlier detection logic
└── ...
```

Each subfolder corresponds to a module or functional area in the codebase.

## Test conventions

The test structure follows these conventions:

- Folder name corresponds to the module being tested
- Test files correspond to specific functions or features
- Test files are named using the pattern:
  `test_<function_or_feature>.py`

Examples:
- `route_cost/test_compute_cost_change.py`
- `greedy/test_greedy_hpp_algorithm.py`
- `core_algorithm/test_find_outliers.py`

## Module usage

Tests are written to be:
- deterministic where possible
- isolated to a single responsibility
- aligned with the public behavior of the corresponding module

Tests do not implement algorithmic logic themselves,
but assert correctness of existing implementations.

The test suite supports:
- validation against exact solvers
- regression testing for heuristics
- verification of edge cases and invariants

## Execution

All tests are compatible with `pytest` and can be executed together
from the project root.

The test structure assumes that:
- the project is importable as a package
- runtime configuration is handled externally where needed