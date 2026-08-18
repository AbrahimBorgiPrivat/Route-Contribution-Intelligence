# OSRM Service – Route Contribution Intelligence

This service implements the **OSRM routing layer (A)** and contributes to the **visualization layer (C)** in the Route Contribution Intelligence System.  
It provides:

1. **Asymmetric distance matrices (D)** for algorithmic processing.  
2. **Route geometry for Folium map visualization**, including encoded polylines and step data.

---

## 1. Purpose

The OSRM service is responsible for:

- Computing **distance matrices** using the OSRM `/table` API.  
- Generating **routes and polyline geometry** using the OSRM `/route` API.  
- Supporting Python components:
  - `OSRMClient`
  - `RoutePlotterFolium`
  - `prepare_route_data()`

These power both **Type 1 & Type 2 outlier detection models** and the **HTML route visualization engine**.

---

## 2. Directory Structure

```text
services/osrm/
│
├── data/
│   ├── maps/           # Contains *.osm.pbf files (raw OSM data)
│   └── osrm/           # Generated OSRM graph files (.osrm, .cells, .partition ...)
│
├── build_data.sh       # Script to build OSRM dataset (extract → partition → customize)
└── docker-compose.yml  # OSRM backend service definition (port 5000)
```

---

## 3. Requirements

- Docker Desktop (Windows/macOS/Linux)  
- Git Bash (required for running the shell script on Windows)  
- Internet connection (to download OSM PBF files)

---

## 4. Download OSM Data

From the project root:

```bash
cd services/osrm/data/maps
curl -o denmark.osm.pbf https://download.geofabrik.de/europe/denmark-latest.osm.pbf
```

For the newyork map run

```bash
cd services/osrm/data/maps
curl -o new-york.osm.pbf https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf
```

After download:

```
services/osrm/data/maps/denmark.osm.pbf
services/osrm/data/maps/new-york.osm.pbf
```

---

## 5. Build OSRM Dataset

From the `services/osrm/` directory:

```bash
git bash
chmod +x build_data.sh
./build_data.sh
```

The script will:

1. Run **osrm-extract**  
2. Run **osrm-partition**  
3. Run **osrm-customize**

Output is written to:

```
services/osrm/data/osrm/
```

---

## 6. Start the OSRM Backend

```bash
docker compose up
```

The service becomes available at:

```
http://localhost:5000
```

### Common OSRM endpoints:

| Endpoint | Description |
|---------|-------------|
| `/table` | Distance matrix |
| `/route` | Route geometry & steps |
| `/nearest` | Nearest street node |
| `/match` | Map matching |

---

## 7. Python Integration in the Route Contribution Intelligence Project

### 7.1 Distance Matrix

```python
from libraries.classes.osrm_api import OSRMClient

client = OSRMClient(base_url="http://localhost:5000")
D = client.table_chunked(locations, chunk_size=50)
```

Used in:

- `prepare_route_data()`  
- Cost and DG calculations (Type 1 & Type 2)  
- Outlier algorithms (Section 5.3–5.5 in documentation)

### 7.2 Route Visualization

```python
from libraries.classes.plot_route import RoutePlotterFolium

plotter = RoutePlotterFolium()
steps = client.route_hamilton_cycle(locations)
plotter.add_route_from_steps(steps, name="Route", color="blue")
plotter.save("example_route.html")
```

This integrates with the HTML generator to embed Folium maps.

---

## 8. Workflow Overview

1. Download `.osm.pbf`  
2. Build OSRM dataset  
3. Start backend server  
4. Run outlier analysis pipeline (Type 1/2)  
5. Generate HTML route maps + index dashboard  

This matches the system architecture described in the Route Contribution Intelligence Project.

---

## 9. Troubleshooting

### Error: *Map file not found*
Ensure:

```
services/osrm/data/maps/denmark.osm.pbf
```

exists.

### Path conversion problems in Git Bash
Use Git Bash and let the script handle path normalization.

### OSRM returns 404
Check the service is running:

```bash
docker ps
curl http://localhost:5000
```

---

## 10. Licensing

OSRM uses OpenStreetMap data under the ODbL license.  
https://www.openstreetmap.org/copyright

---

## 11. Maintainer

This OSRM integration is part of the Route Contribution Intelligence Project.

Maintainer: **Abrahim Borgi**

