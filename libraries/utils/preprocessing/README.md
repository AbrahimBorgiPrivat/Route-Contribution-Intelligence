# preprocessing

This folder contains functions for preprocessing raw route and address data.

The goal is to ensure that all algorithmic components
receive consistent and well-defined inputs.

## Structure

```
preprocessing/
├── osrm/               # OSRM -specific data handling
├── osm/                # OSM Snapping -specific data handling
└── route_data_preparer.py   # Cleans and structures raw route data
```

## Module usage

Preprocessing functions are used early in pipelines
and are independent of the specific algorithm being applied.
