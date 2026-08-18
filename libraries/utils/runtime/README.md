# runtime

This folder contains runtime-related helper utilities.

It centralizes logic related to configuration and dynamic parameters
used during execution.

## Structure

```
runtime/
└── runtime_loader.py   # Loads runtime configuration and parameters
```

## Module usage

Runtime utilities are used by pipelines and runners
to decouple configuration handling from algorithmic code.
