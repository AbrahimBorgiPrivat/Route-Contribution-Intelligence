# Runtime definitions

This directory contains **configuration-driven runtime definitions** used to
execute pipelines in a reproducible and environment-independent way.

Runtime definitions decouple *what is executed* from *how it is implemented* by
providing structured configuration files that map directly to pipeline entry
points.

> **Key idea:**  
> Pipelines are pure orchestration code.  
> Runtime definitions supply all execution parameters.

---

## High-level concept

Each runtime definition corresponds to **one pipeline entry point**.
A runtime definition consists of:

- a `runner.json` file containing all parameters
- optional supporting files (e.g. KPI registries)
- a folder structure that mirrors pipeline versioning

Runtime definitions are consumed by runner scripts in:

```
libraries/runners/
```

---

## Current structure

```
runtime_definitions/
├── application/
│   └── demo_bus_routes_nyc/
│       ├── runner.json
│       └── __init__.py
│
├── static/
│   └── demo_bus_routes_nyc/
│       ├── runner.json
│       ├── kpi_registry.py
│       └── __init__.py
│
├── README.md
└── __init__.py
```

---

## Application pipeline runtime (`application/v1`)

**Purpose**

Drives the **application data pipeline**, which produces machine-readable
outputs such as GeoJSON and JSON indices.

**Pipeline executed**

```
libraries/utils/pipelines/pipelines/application/v1/run_route_data_pipeline.py
```

**Typical outputs**

- `routes/<route_id>/<route_id>_markers.geojson`
- `routes/<route_id>/<route_id>_route.geojson`
- `routes/<route_id>/<route_id>.json`
- `routes_index.json`

**Configuration sections**

`runner.json` typically contains:

- `input`
  - dataset paths
- `output`
  - save directories
- `routing`
  - route selection (`route_type`, `start_routes`, `max_routes`)
- `algorithm`
  - optimization and outlier parameters
- `geometry`
  - OSM / OSRM / structured routing parameters
- `col_map`
  - dataset column mappings
- `kpis`
  - KPI definitions for index generation
- `flags`
  - pipeline behavior toggles (e.g. `use_data`)

---

## Static presentation pipeline runtime (`static/v1`)

**Purpose**

Drives the **static presentation pipeline**, which produces human-facing
outputs such as HTML pages and interactive maps.

**Pipeline executed**

```
libraries/utils/pipelines/pipelines/static/v1/run_route_presentation_pipeline.py
```

**Typical outputs**

- `maps/route_<id>_map.html`
- `routes/route_<id>.html`
- `maps/all_routes_map.html`
- `index.html`

**Additional files**

- `kpi_registry.py`
  - Defines how KPIs are computed and displayed in the UI

---

## Versioning strategy

- Runtime definitions are **versioned by folder**, not by file name.
- Each version maps to a specific pipeline entry point.
- Older versions remain runnable as long as their pipeline exists.

This allows:
- backward compatibility
- parallel experimentation
- controlled evolution of outputs and behavior

---

## Execution flow

1. A runner script loads a runtime directory
2. `runner.json` is parsed into a configuration object
3. Configuration values are mapped to pipeline function arguments
4. The pipeline is executed without modifying code

This guarantees:
- reproducibility
- clear provenance of results
- easy automation (batch jobs, CI, cron)

---

## Extending runtime definitions

To add a new runtime:

1. Create a new subfolder (e.g. `application/v2`)
2. Add a `runner.json`
3. Optionally add supporting files (registries, schemas)
4. Point a runner script to the new directory

No code changes are required unless a new pipeline entry point is introduced.

---

## Summary

- Runtime definitions are the **configuration layer** of the system
- They mirror pipeline structure and versioning
- All execution behavior is driven from JSON
- This design enables scalable, testable, and reproducible runs
