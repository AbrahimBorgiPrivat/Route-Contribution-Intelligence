# visualization

This folder contains functionality for generating visualization outputs.

It focuses exclusively on presentation and does not perform
any algorithmic computation.

## Structure
```
visualization/
├── geojson_pipeline.py        # Builds GeoJSON structures for routes and markers
├── html_generator.py          # Generates HTML output
├── map_pipeline.py            # Assembles map visualizations
└── visualisation_helpers.py   # Shared visualization utilities
```
## Module usage

Visualization modules consume precomputed results
and transform them into formats suitable for presentation,
such as maps and static HTML pages.
