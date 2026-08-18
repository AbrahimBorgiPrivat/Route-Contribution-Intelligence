# Runners

This directory contains **runner modules** that act as the execution entry points
for pipelines. Runners are responsible for *binding runtime configuration* to
*pipeline execution*.

> **Key rule:**  
> Runners do **not** implement business logic.  
> They only translate runtime definitions into pipeline function calls.

---

## Conceptual role

In the overall system architecture:

- **Pipelines** define *what happens* (orchestration of steps)
- **Runtime definitions** define *how it should run* (configuration)
- **Runners** connect the two

A runner:
1. Loads a runtime definition directory
2. Parses `runner.json` and supporting files
3. Maps configuration fields to pipeline arguments
4. Executes the pipeline

This keeps execution:
- reproducible
- configurable
- decoupled from code changes

---

## Directory structure

```
libraries/runners/
├── application/
│   └── v1/
│       ├── run_data_pipeline.py
│       └── __init__.py
│
├── static/
│   └── v1/
│       ├── run_presentation_pipeline.py
│       └── __init__.py
│
├── README.md
└── __init__.py
```

---

## Application runners

### `application/v1/run_data_pipeline.py`

**Purpose**

Executes the **application data pipeline**, which produces machine-readable
outputs such as GeoJSON and JSON indices.

**Pipeline invoked**

```
libraries/utils/pipelines/pipelines/application/v1/run_route_data_pipeline.py
```

**Typical usage**

```bash
python -m libraries.runners.application.v1.run_data_pipeline   
```

**Responsibilities**

- Load runtime definition
- Map algorithm, routing, geometry, and dataset parameters
- Invoke the data pipeline
- Return or log pipeline outputs

---

## Static presentation runners

### `static/v1/run_presentation_pipeline.py`

**Purpose**

Executes the **static presentation pipeline**, producing HTML pages and maps
for human inspection.

**Pipeline invoked**

```
libraries/utils/pipelines/pipelines/static/v1/run_route_presentation_pipeline.py
```

**Typical usage**

```bash
python -m libraries.runners.static.v1.run_presentation_pipeline   
```

**Responsibilities**

- Load runtime definition
- Resolve KPI registry
- Map presentation-specific parameters
- Invoke the static pipeline

---

## Versioning strategy

- Runners are versioned by folder (`v1`, `v2`, …)
- Each runner version maps to a specific pipeline version
- Multiple versions can coexist safely

This allows:
- backward compatibility
- controlled rollout of new behavior
- reproducible historical runs

---

## Design guarantees

- No algorithmic logic inside runners
- No filesystem assumptions beyond runtime paths
- No hard-coded defaults (defaults live in pipelines)
- One runner = one pipeline entry point

---

## Extending runners

To add a new runner:

1. Create a new subfolder (e.g. `application/v2`)
2. Implement a runner that:
   - loads runtime context
   - maps configuration fields
   - calls a pipeline
3. Add a corresponding runtime definition

Pipelines and runners evolve independently but remain structurally aligned.

---

## Summary

- Runners are the **execution glue** of the system
- They translate configuration into pipeline execution
- They enforce reproducibility and consistency
- They keep pipelines clean and reusable
