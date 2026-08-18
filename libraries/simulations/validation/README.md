# validation

This folder contains validation scripts used to assess correctness
and robustness of the implemented algorithms.

Validation focuses on comparing heuristic and hybrid methods
against exact or reference solutions.

## Structure

```
validation/
├── validate_exact_vs_heuristic.py   # Validation of solvers against exact baselines
├── validate_outliers_vs_exact.py    # Validation of outlier detection methods
└── ...
```

Additional validation scripts may be added as new models or methods require verification.

## Module usage

Validation scripts rely on exact solvers, heuristic methods,
and simulation utilities to quantify deviations and failure cases.
Results are typically summarized using plots stored in `_img`.
