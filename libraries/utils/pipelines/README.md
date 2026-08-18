# Pipelines

This directory contains the **pipeline architecture** for the route optimization system.
Pipelines are responsible for *orchestrating* data flow between preprocessing,
algorithms, and application-level outputs.  

> **Important principle:**  
> Pipelines do **not** implement algorithmic logic.  
> They compose and coordinate existing components in a clear, testable structure.

---

## High-level design

The pipeline system is organized into **four conceptual layers**:

1. **Context layer (A)**  
   Load and normalize datasets, resolve route selection, and prepare global runtime context.

2. **Route preparation layer (B)**  
   Build per-route inputs: coordinates, OSM/OSRM geometry, distance matrices, and
   structured routing artifacts.

3. **Algorithm layer (C)**  
   Execute optimization and outlier-detection algorithms on prepared routes.

4. **Application layer (D)**  
   Turn algorithm outputs into concrete artifacts:
   - data products (GeoJSON, JSON indices)
   - static presentation products (maps, HTML pages)

The `pipelines/` folder then exposes **versioned pipeline entry points**
that glue these layers together.

---

## Directory structure

```
libraries/utils/pipelines/
├── a_context_layer/
│   └── pipeline_dataset_context.py
│       Load dataset, normalize inputs, select routes.
│
├── b_route_preparation_layer/
│   └── pipeline_prepare_route.py
│       Prepare a single route (geometry, OSRM/OSM data, structured routing).
│
├── c_algorithm_layer/
│   └── pipeline_outlier_detection_for_route.py
│       Run outlier detection and optimization algorithms.
│
├── d_application_layer/
│   ├── application/
│   │   └── V1/
│   │       ├── pipeline_ap_vone_route_data.py
│   │       │   Build per-route data artifacts (GeoJSON, metadata).
│   │       └── pipeline_ap_vone_index_data.py
│   │           Build global data index (routes_index.json).
│   │
│   └── static/
│       └── V1/
│           ├── pipeline_st_vone_route_presentation.py
│           │   Render per-route static presentation (maps, route pages).
│           └── pipeline_st_vone_index_presentation.py
│               Render global static presentation (index page, combined map).
│
└── pipelines/
    ├── application/
    │   └── v1/
    │       └── run_route_data_pipeline.py
    │           Entry point for the **data pipeline** (GeoJSON + JSON outputs).
    │
    └── static/
        └── v1/
            └── run_route_presentation_pipeline.py
                Entry point for the **static presentation pipeline** (HTML + maps).
```

---

## Pipeline entry points

### Data pipeline (Application / V1)

**Location**
```
pipelines/application/v1/run_route_data_pipeline.py
```

**Purpose**
- Iterate selected routes
- Prepare route data (A + B)
- Run algorithms (C)
- Generate per-route GeoJSON and metadata
- Generate a global `routes_index.json`

**Typical outputs**
- `routes/<route_id>/<route_id>_markers.geojson`
- `routes/<route_id>/<route_id>_route.geojson`
- `routes/<route_id>/<route_id>.json`
- `routes_index.json`

---

### Static presentation pipeline (Static / V1)

**Location**
```
pipelines/static/v1/run_route_presentation_pipeline.py
```

**Purpose**
- Iterate selected routes
- Prepare route data (A + B)
- Run algorithms (C)
- Render static visual outputs (maps, HTML pages)
- Render global index and combined map

**Typical outputs**
- `maps/route_<id>_map.html`
- `routes/route_<id>.html`
- `maps/all_routes_map.html`
- `index.html`

---

## Versioning strategy

- **Versioning lives at the pipeline entry-point level**, not inside core logic.
- Shared logic remains reusable across versions.
- New behavior is introduced by adding new `Vx/` folders under:
  - `d_application_layer/application/`
  - `d_application_layer/static/`
  - `pipelines/application/`
  - `pipelines/static/`

This makes it possible to:
- maintain backward compatibility
- evolve presentation or data formats independently
- test each version in isolation

---

## Testing philosophy

Each layer and pipeline entry point is covered by tests:

- Unit-style tests for small helpers (e.g. GeoJSON utilities)
- Integration-style tests for:
  - route preparation
  - algorithm execution
  - application-layer outputs
  - full pipeline runs

Tests are written to reflect **real runtime usage** by driving pipelines
through configuration-like inputs rather than hard-coded values.

---

## Summary

- Pipelines orchestrate, they do not compute.
- Clear separation of concerns across layers.
- Symmetric design between data and presentation pipelines.
- Versioned entry points enable safe evolution.

This structure is designed to scale as new routing modes,
output formats, and application variants are added.
