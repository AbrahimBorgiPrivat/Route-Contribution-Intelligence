# _data

This folder contains data files used as input for simulations,
benchmarks, and validation.

The data includes both synthetic datasets and subsampled real-route data
constructed to support controlled experiments.

## Structure

```
_data/
├── routes/     # Route and address datasets (synthetic and real)
├── runners/    # Runtime and configuration definitions for simulations
└── ...
```

New datasets may be added to support additional experiments or scenarios.

## Module usage

Data in this folder is consumed by simulation and validation scripts
and passed through preprocessing and pipeline utilities before use
in algorithms.
