# Route Contribution Intelligence

This repository contains a configuration-driven toolkit for analyzing route-level contribution, travel cost, and economic outliers.

The codebase is organized around four separate concerns:

- `libraries/` holds reusable Python logic for preprocessing, routing, optimization, pipelines, and tests
- `runtime_definitions/` holds local runtime configurations used by runner modules
- `services/` holds Docker-based service entry points and supporting routing infrastructure
- `views/` holds browser-facing outputs in both static and interactive form

The current public demo scenario is `demo_bus_routes_nyc`, which uses New York MTA bus-stop data to show the full flow from prepared route input to rendered application and static views.

---

## Conceptual model overview

The core problem addressed by the project is to understand how individual addresses contribute to (or detract from) the economic performance of a delivery route.

At a conceptual level, each route consists of:
- a set of addresses (nodes)
- a traversal order (route structure)
- a distance or travel cost model
- a revenue model (e.g. revenue per address)
- an economic penalty model (APR, distance cost, etc.)

The project evaluates the **marginal economic effect** of removing one or more addresses from a route.  
Addresses whose removal improves overall route profitability are considered potential outliers.

This evaluation is performed under different modeling assumptions, leading to three model types.

---

## Model types (aligned with the report)

### Type 1 — Fixed route order

Type 1 assumes that the visiting order of the route is fixed and cannot be changed.

Characteristics:
- route order is given and preserved
- marginal effects are evaluated without re-optimizing the route
- computationally simple and highly interpretable
- suitable as a baseline model

Type 1 is primarily used to:
- analyze existing operational routes
- establish baseline profitability
- compare against more flexible models

---

### Type 2 — Optimized route order

Type 2 allows the visiting order of the route to change when addresses are removed.

Characteristics:
- route order is optimized after removals
- supports multiple solvers (heuristic and exact)
- captures structural effects of route changes
- higher computational cost than Type 1

Type 2 is central to the project and is used to:
- evaluate true marginal impact under optimal routing
- compare solver behavior and performance
- study sensitivity to routing assumptions

---

## Repository structure

```text
outlier_project/
|-- data/
|-- docs/
|-- libraries/
|-- runtime_definitions/
|-- services/
|-- views/
|-- requirements.txt
`-- pytest.ini
```

### `data/`

Input data lives here.

This includes both raw source files and prepared route-model inputs such as:

- `data/routes.csv`
- `data/route_revenue.csv`
- raw MTA extracts used to build the demo scenario

### `libraries/`

Core Python code.

Important areas:

- `libraries/utils/`
  Preprocessing, runtime loading, shared helpers, and pipeline orchestration
- `libraries/runners/`
  Thin entry points that bind a runtime definition to a pipeline
- `libraries/tests/`
  Test coverage for the reusable logic
- `libraries/simulations/`
  Experiment and simulation support

### `runtime_definitions/`

Local runtime definitions for direct execution from the repository.

Current application runtimes:

- `runtime_definitions/application/v1`
- `runtime_definitions/application/v2`
- `runtime_definitions/application/demo_bus_routes_nyc`

Current static runtimes:

- `runtime_definitions/static/v1`
- `runtime_definitions/static/demo_bus_routes_nyc`

Each runtime is centered around a `runner.json` file and, where needed, supporting files such as KPI registries.

### `services/`

Operational wrappers and infrastructure support.

Main folders:

- `services/route_pipelines/`
  Docker-based pipeline execution
- `services/osrm/`
  OSRM-related assets and map builds
- `services/osm/`
  OSM-related helpers

The route pipeline compose file currently includes:

- `route-data-v1`
- `route-data-v2`
- `route-data-demo-bus-routes-nyc`
- `route-presentation-v1`
- `route-presentation-demo-bus-routes-nyc`

### `views/`

User-facing outputs.

```text
views/
|-- static/
|   |-- v1/
|   `-- demo_bus_routes_nyc/
`-- application/
    |-- v1/
    |-- v2/
    `-- demo_bus_routes_nyc/
```

- `views/static/...`
  Batch-rendered HTML output
- `views/application/...`
  Browser-based interactive views backed by JSON and GeoJSON

### `docs/`

Project documentation.

- `docs/pages/`
  Static HTML documentation site
- `docs/report/`
  LaTeX-based report material

## How the project is structured

The execution model is intentionally simple:

1. Data is prepared into route-level inputs.
2. A runner loads a runtime definition.
3. A pipeline executes preprocessing, routing, and analysis.
4. Results are written into a target `views/` folder.
5. Static pages or browser applications render the output.

This keeps algorithm code separate from configuration and separate again from presentation.

## Getting started

Create a virtual environment and install dependencies from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run commands from the repository root unless a section says otherwise.

## Local runner commands

Use module execution so imports resolve correctly.

### Application runners

```powershell
python -m libraries.runners.application.demo_bus_routes_nyc.run_data_pipeline
python -m libraries.runners.application.demo_bus_routes_nyc_single_scenario.run_data_pipeline
```

### Static runners

```powershell
python -m libraries.runners.static.demo_bus_routes_nyc.run_presentation_pipeline
```

## Demo scenario: `demo_bus_routes_nyc`

This demo uses prepared route inputs in:

- `data/routes.csv`
- `data/route_revenue.csv`

It also uses the dedicated runtime definitions and view folders named `demo_bus_routes_nyc`.

### Generate application output

```powershell
python -m libraries.runners.application.demo_bus_routes_nyc.run_data_pipeline
```

### Generate static output

```powershell
python -m libraries.runners.static.demo_bus_routes_nyc.run_presentation_pipeline
```

### Open the interactive application locally

```powershell
cd views\application\demo_bus_routes_nyc
python -m http.server 8011
```

Then open:

```text
http://127.0.0.1:8011/html/index.html
```

The application is static frontend code, so no dedicated backend server is required.

## Docker-based pipeline execution

Docker-based runs are defined in:

```text
services/route_pipelines/docker-compose.yml
```

Run from `services/route_pipelines/` for example:

```powershell
docker compose up route-data-demo-bus-routes-nyc
docker compose up route-presentation-demo-bus-routes-nyc
```

The compose setup also exposes routing service URLs through environment variables, including a dedicated New York car profile endpoint.

## Documentation

The documentation site lives in `docs/pages/`.

To preview it locally:

```powershell
cd docs\pages
python -m http.server 8012
```

Then open:

```text
http://127.0.0.1:8012/
```

The documentation explains:

- the analytical problem
- the graph and contribution-margin framing
- the solution families
- the demo data and example implementations

## Testing

The repository uses `pytest`.

Typical command:

```powershell
pytest
```

If you want to scope the run:

```powershell
pytest libraries/tests
```

## Notes on versioning

The repository keeps multiple generations side by side.

- `demo_bus_routes_nyc` is the current public example-oriented scenario
- runtime definitions, runners, and views are versioned independently but follow the same overall structure

This allows new scenarios to be added with minimal impact on existing flows.
