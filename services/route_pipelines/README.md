# Route Pipeline Services

Docker-servicer til:

- `libraries/runners/application/v1/run_data_pipeline.py`
- `libraries/runners/application/v2/run_data_pipeline.py`
- `libraries/runners/application/demo_bus_routes_nyc/run_data_pipeline.py`
- `libraries/runners/static/v1/run_presentation_pipeline.py`
- `libraries/runners/static/demo_bus_routes_nyc/run_presentation_pipeline.py`

Koden bliver kopieret ind i image ved build, mens kun de runtime-relevante mapper mountes ind via compose:

- `data/`
- `views/application/v1`
- `views/application/v2`
- `views/application/demo_bus_routes_nyc`
- `views/static/v1`
- `views/static/demo_bus_routes_nyc`
- service-specifikke `runtime_definitions/`

Begge services er sat op med `max_routes: 2` i deres service-runtime, så de kan køres som en hurtig smoke test.

Kør fra denne mappe:

```powershell
docker compose up --build route-data-v1
docker compose up --build route-data-v2
docker compose up --build route-data-demo-bus-routes-nyc
docker compose up --build route-presentation-v1
docker compose up --build route-presentation-demo-bus-routes-nyc
```

Hvis OSRM/OSM kører på andre adresser end standardportene på værten, kan de overrides med miljøvariablerne:

- `OSM_SNAP_URL`
- `OSRM_FOOT_URL`
- `OSRM_CAR_URL`
- `OSRM_CAR_NEWYORK_URL`
- `OSRM_BICYCLE_URL`
