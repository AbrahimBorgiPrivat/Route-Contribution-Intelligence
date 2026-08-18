# structural_heuristics

This folder contains structural heuristics used to reduce the search space
in outlier detection and hybrid algorithms.

The heuristics identify promising candidate structures
before more expensive evaluation is performed.

## Structure

```
structural_heuristics/
├── beam_method.py                # Beam-based expansion of candidate sets
├── find_marginal_blocks.py       # Identification of marginal blocks
└── greedy_peripheral_clusters.py # Detection of peripheral clusters
```

## Module usage

Structural heuristics are invoked by higher-level algorithms
(e.g. `core_algorithm.py`) to generate candidate subsets S.

They do not compute final decisions themselves,
but guide which structures are evaluated in detail.
