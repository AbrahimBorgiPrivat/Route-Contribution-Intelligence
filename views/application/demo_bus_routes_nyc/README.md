# demo_bus_routes_nyc - New York Bus Route Demo

## Overview

`demo_bus_routes_nyc` is a static frontend for exploring pre-generated route optimization output.

It does not run optimization itself.
It reads `JSON` and `GeoJSON` files from `views/application/demo_bus_routes_nyc/data/`.

## Run locally

Run the app as static files from the `views/application/demo_bus_routes_nyc/` folder:

```powershell
cd views\application\demo_bus_routes_nyc
python -m http.server 8011
```

Then open:

```text
http://127.0.0.1:8011/html/index.html
```

Do not open the HTML files directly with `file://`, because the frontend uses `fetch(...)` for registry, route JSON, and GeoJSON files.

## Entry pages

- `html/index.html`
  Multi-scenario entry page with filters and scenario overview.
- `html/overview.html`
  Scenario page for one selected label/profile/analysis period.
- `html/route.html`
  Route detail page for one selected route.

## Required query parameters

- `overview.html`
  `label`, `apr`, `week`
- `route.html`
  `label`, `route_id`, `apr`, `week`

The URL parameter is still called `week`, but in the UI it is shown as `Analysis period`.

## Main data files

- `data/registry.json`
  Registry of available scenario/route combinations.
- `data/scenario_metadata.json`
  Optional explanations for labels, profiles, and analysis periods.

## Folder structure

```text
views/application/demo_bus_routes_nyc/
|-- css/
|-- data/
|-- html/
|-- img/
|-- js/
|-- favicon.ico
`-- README.md
```

## Notes

- `demo_bus_routes_nyc` is served with a simple local HTTP server.
- No dedicated backend server is required.
- If the browser shows stale files, use a hard refresh after changes.
