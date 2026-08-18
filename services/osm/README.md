# OSM Snap Service

## Introduction

The **OSM Snap Service** is a high-performance geospatial service for snapping arbitrary input coordinates to **junction-bounded OpenStreetMap road segments**.

It is designed to complement **OSRM**, not replace it.

- **OSRM** answers: *How do I get from A to B?*
- **OSM Snap** answers: *Which exact road segment and junction does this point belong to?*

The service focuses on **topology, segmentation, and turn structure**, while OSRM focuses on **routing and travel times**.

Typical use cases include:
- address-to-road assignment
- postal and delivery route analysis
- route outlier detection
- preprocessing for optimization models
- structural analysis of road networks

---

## Problem Statement

Given an input point `(x, y)` in some coordinate reference system (CRS):

- find the **nearest valid road segment**
- where a segment is defined as **the portion of a road between two junctions**
- return:
  - the projected point on the road
  - segment metadata
  - entry and exit junction nodes
  - available turns at those nodes
  - side of road (left / right / center)

This cannot be solved correctly using routing engines alone, because routing engines:
- do not expose junction-bounded segments
- do not expose full turn topology
- are optimized for shortest-path queries, not structural analysis

---

## High-level Architecture

```
services/osm/
│
├── app/                         # Runtime (Docker / FastAPI)
│   ├── main.py                  # Application entrypoint
│   ├── config.py                # Runtime configuration
│   │
│   ├── runtime/                 # Pure runtime logic (no I/O)
│   │   ├── errors.py            # Class for all expected errors
│   │   ├── index.py             # Snap + query logic
│   │   ├── loader.py            # Build-artifact loader
│   │   └── types.py             # Immutable runtime types
│   │
│   └── service/
│       ├── server.py            # FastAPI HTTP layer
│       └── dependencies.py      # Dependency injection
│
├── build/                       # Offline build pipeline
│   ├── paths.py                 # Build-time filesystem layout
│   ├── config.py                # Highway selection (memory control)
│   ├── build_osm_snap_index.py  # Build entrypoint
│   └── classes/
│       ├── osm_highway_extractor.py
│       └── snap_index_builder.py
│
├── tests/                       # Test suite
│   ├── api/                     # HTTP / FastAPI tests
│   │   ├── test_health.py
│   │   ├── test_snap_nearest.py
│   │   └── test_turns.py
│   │
│   ├── integration/             # Real-data integration tests
│   │   ├── test_snap_nearest_real.py
│   │   ├── test_segment_geometry.py
│   │   ├── test_turns_consistency.py
│   │   └── test_golden_dataset.py
│   │
│   ├── unit/                    # Pure logic unit tests
│   │   ├── test_classify_side.py
│   │   ├── test_turn_helpers.py
│   │   └── test_segment_helpers.py
│   │
│   └── conftest.py              # Shared pytest fixtures
│
├── data/
│   ├── maps/                    # Raw OSM input (ignored by git)
│   └── build/                   # Build artifacts (mounted read-only)
│
├── .env                         # Should be included -use .env_example as template
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Relationship to OSRM

| Component | Responsibility |
|----------|----------------|
| **OSRM** | Routing, shortest paths, travel times |
| **OSM Snap** | Road segmentation, junctions, turns, projection |

Both services:
- use the **same OSM PBF source**
- are built independently
- run side-by-side in Docker

OSRM does **not** expose:
- which junction-bounded segment a point belongs to
- where a segment starts and ends
- which turns exist at a junction

OSM Snap provides exactly this missing structural information.

---

## Build Phase (Offline)

### 1. Download OpenStreetMap data

The OSM Snap Service uses the **same PBF file as OSRM**.

From the project root:

```bash
cd services/osrm/data/maps
curl -o denmark.osm.pbf https://download.geofabrik.de/europe/denmark-latest.osm.pbf
```

After download, the file is located at:

```
services/osrm/data/maps/denmark.osm.pbf
```

---

### 2. Build the snap index

From the project root:

```bash
python -m services.osm.build.build_osm_snap_index
```

The build pipeline performs the following steps:

1. Filter OSM ways to selected highway types  
2. Split ways into junction-bounded segments  
3. Compute explicit turn relations at junctions  
4. Build spatial STRtree indexes (GEOS)  
5. Persist optimized runtime artifacts  

All artifacts are written to:

```
services/osm/data/build/
```

Memory usage at runtime is **entirely determined at build time** by the selected highway types.

---

## Runtime Service

### Build and start the container

```bash
docker compose build osm-snap
docker compose up osm-snap
```

The service will be available at:

```
http://localhost:5010
```

---

## HTTP API

### Health

**GET** `/health`

Response:

```json
{ "status": "ok" }
```

---

### Snap nearest segment

**POST** `/snap/nearest`

Request:

```json
{
  "x": 863994,
  "y": 6123307,
  "input_crs": "EPSG:25832",
  "output_crs": "EPSG:4326",
  "allowed_highways": ["residential", "secondary", "tertiary"]
}
```

Response (example):

```json
{
  "input": {
    "x": 863994,
    "y": 6123307,
    "crs": "EPSG:25832"
  },
  "segment": {
    "segment_id": 155223,
    "osmid": 26965271,
    "highway": "residential",
    "name": "Examplevej",
    "entry_node": 6167898645,
    "exit_node": 295563554
  },
  "projected_point": {
    "x": 14.70523,
    "y": 55.10081,
    "crs": "EPSG:4326"
  },
  "geometry": {
    "entry_point": {
      "x": 14.70520,
      "y": 55.10079,
      "node_id": 6167898645,
      "turns": [
        {
          "turn_id": 1031107,
          "to_segment": 155222,
          "angle_deg": 0.02
        }
      ]
    },
    "exit_point": {
      "x": 14.70526,
      "y": 55.10084,
      "node_id": 295563554,
      "turns": null
    },
    "side_of_road": "left",
    "crs": "EPSG:4326"
  }
}
```

---

### Snap nearest (batch)

**POST** `/snap/nearest/batch`

```json
{
  "points": [
    [863994, 6123307],
    [863973, 6123314],
    [863956, 6123159]
  ],
  "input_crs": "EPSG:25832",
  "output_crs": "EPSG:4326"
}
```

Returns a list of snap results in the same format as `/snap/nearest`.

---

### Segment & Turn Queries

- **GET** `/segments/{segment_id}`  
  Returns segment geometry and metadata

- **GET** `/segments/{segment_id}/turns`  
  Returns all outgoing turns from a segment

- **GET** `/nodes/{node_id}/turns`  
  Returns all turns at a junction node

- **GET** `/turns/{turn_id}`  
  Returns full turn metadata

---

## Performance & Memory

- High memory usage is expected due to GEOS STRtrees
- Runtime memory usage is controlled **at build time**
- Reduce indexed highways in `build/config.py` to reduce RAM
- Enable lazy STRtree loading:

```env
OSM_SNAP_LAZY_TREES=true
```

---

## Error Handling

The OSM Snap Service returns structured error responses for all expected
failure modes. Unexpected internal failures are returned as generic
**500 Internal Server Error** responses.

---

### Error Response Format

When an error occurs, the service returns a JSON object with the following
structure:

    {
      "error": "ErrorType",
      "message": "Human-readable explanation",
      "hint": "Optional guidance",
      "endpoint": "/api/endpoint"
    }

**Fields**

- **error** – Machine-readable error type  
- **message** – Short explanation of what went wrong  
- **hint** – Optional suggestion for resolving the issue  
- **endpoint** – API endpoint where the error occurred  

---

### Common Error Codes

#### 400 Bad Request

Returned when the request is syntactically valid but cannot be processed.

**Typical causes**
- No road segment found near the input coordinates
- All candidate segments filtered out by `allowed_highways`
- Coordinates outside the indexed road network

**Example**

    {
      "error": "NoSegmentFoundError",
      "message": "No segment found for given coordinates and filters.",
      "hint": "Check input_crs and allowed_highways.",
      "endpoint": "/snap/nearest/batch"
    }

---

#### 422 Unprocessable Entity

Returned when input parameters are invalid or inconsistent.

**Typical causes**
- Invalid or unsupported CRS
- Invalid highway types in `allowed_highways`

**Example**

    {
      "error": "InvalidCRSError",
      "message": "Invalid or unsupported CRS: EPSG:999999",
      "hint": "Check input_crs parameter.",
      "endpoint": "/snap/nearest"
    }

---

#### 500 Internal Server Error

Returned only for unexpected internal failures.

**Examples**
- Corrupted runtime data
- Missing index files
- Unhandled programming errors

In these cases, the response body may contain only:

    Internal Server Error

---

### Client Behaviour

Clients should:

- Treat **4xx** errors as actionable input feedback
- Surface the returned **message** and **hint** directly to users
- Treat **5xx** errors as non-recoverable service failures

The reference Python client prints the server response verbatim when an
error occurs.

---

## Testing

The OSM Snap Service includes a comprehensive, layered test suite designed to
ensure correctness, stability, and confidence when working with large-scale
geospatial data.

The test strategy follows best practice for geospatial services by separating
pure logic tests, real-data integration tests, and API-level contract tests.

---

### Test Structure

```text
services/osm/tests/
├── unit/            # Fast, isolated logic tests (no OSM data)
├── integration/     # Real-data tests using build artifacts
├── api/             # FastAPI HTTP endpoint tests
└── conftest.py      # Shared fixtures (snap index, test client)
```

---

## Status

- Build pipeline: **Stable**
- Runtime service: **Stable**
- Dockerized: **Yes**

## Policy

### Data Sources

This service uses data from **OpenStreetMap (OSM)**.

- Source: https://www.openstreetmap.org  
- License: **Open Database License (ODbL) v1.0**

The OSM Snap Service does **not modify** OpenStreetMap data.  
Instead, it derives secondary artifacts by:

- filtering highway features
- splitting roads into junction-bounded segments
- computing explicit turn topology
- building spatial indexes (STRtrees)

These outputs are considered **Produced Works** under the ODbL.

---

### Data Usage Policy

- Raw OSM `.osm.pbf` files are **not redistributed** by this service.
- Derived build artifacts are intended for **internal use** or **controlled deployment**.
- Any public redistribution of derived datasets must comply with the ODbL:
  - share-alike obligations may apply if datasets are redistributed

---

### Service Usage Policy

- The service is designed for **offline preprocessing and analysis**, not end-user navigation.
- No personal data is processed or stored by the service.
- All computations are performed on static geographic data and user-provided coordinates.

---

### Performance & Resource Policy

- High memory usage is expected due to in-memory spatial indexes (GEOS STRtrees).
- Memory footprint is controlled **at build time** by limiting indexed highway classes.
- Runtime memory usage should be monitored in production environments.

---

## License

### Code License

Unless otherwise stated, the **source code of this project** is licensed under the **MIT License**.

You are free to:
- use
- modify
- distribute
- sublicense

the code, subject to the conditions of the MIT License.

---

### Data License (OpenStreetMap)

OpenStreetMap data is licensed under the **Open Database License (ODbL) v1.0**.

© OpenStreetMap contributors

- https://opendatacommons.org/licenses/odbl/1-0/
- https://www.openstreetmap.org/copyright

The MIT License **does not apply** to OpenStreetMap data or derived datasets.

---

### Attribution Requirement

If this service or its outputs are used in a user-facing product, the following attribution is required:

> “Contains data © OpenStreetMap contributors.”

---

### Disclaimer

This software is provided **“as is”**, without warranty of any kind.

The authors:
- make no guarantees about data correctness
- are not responsible for routing decisions
- are not responsible for real-world navigation outcomes

## Contact

For questions, feedback, or collaboration related to this project, please contact:

**Abrahim Borgi**  
Senior Data Analyst   

