# osrm

This folder contains functionality related to OSRM-based routing data.

It isolates all logic that depends on external routing services
from the rest of the algorithmic code.

## Structure

```
preprocessing/
└── osrm/
    └── osrm_data.py   # Loading and processing OSRM routing responses
```

## Module usage

OSRM utilities are used during preprocessing and route construction.
The algorithm layer consumes only processed distance and path data,
not raw OSRM responses.
