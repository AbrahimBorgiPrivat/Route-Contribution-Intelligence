# classes

This folder contains higher-level classes that encapsulate
reusable functionality related to data construction, external interfaces,
and presentation.

The classes here typically wrap lower-level utilities
into coherent objects with clearly defined responsibilities.

## Structure

```
classes/
├── geojson_builder.py   # Class-based construction of GeoJSON structures for routes and markers
├── osrm_api.py          # Encapsulation of OSRM API interaction and response handling
├── plot_route.py        # Class for rendering and exporting route visualizations
└── ...
```

Additional classes may be added as the project evolves.

## Module usage

Classes in this folder are used by pipelines and visualization layers
to structure interactions with external services and to organize
complex output generation.

They provide a higher-level abstraction than the utility functions
found in `utils`, while remaining free of algorithmic logic.