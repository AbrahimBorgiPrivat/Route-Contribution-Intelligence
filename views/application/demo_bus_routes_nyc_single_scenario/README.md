# demo_bus_routes_nyc_single_scenario

## Overview

`demo_bus_routes_nyc_single_scenario` is a single-scenario application view for the New York MTA demo data.

It uses the v1-style application data layout:

- one `routes_index.json`
- one folder per route
- no scenario selector in the frontend

The scenario is fixed to:

- `Label`: `All Routes`
- `Profile`: `MTA Car New York`
- `Analysis period`: `MTA 2024-10-15`

## Generate data

Run from the repository root:

```powershell
python -m libraries.runners.application.demo_bus_routes_nyc_single_scenario.run_data_pipeline
```

This writes output to:

```text
views/application/demo_bus_routes_nyc_single_scenario/data/
```

## Run locally

Serve the frontend over HTTP:

```powershell
cd views\application\demo_bus_routes_nyc_single_scenario
python -m http.server 8013
```

Then open:

```text
http://127.0.0.1:8013/html/index.html
```

Do not open the HTML files directly with `file://`, because the frontend loads JSON and GeoJSON with `fetch(...)`.
