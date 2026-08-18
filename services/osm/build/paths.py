from __future__ import annotations
from pathlib import Path

# ==================================================
# Build-time filesystem layout
# ==================================================

OSM_PBF: Path = Path("services/osrm/data/maps/denmark.osm.pbf")
FILTERED_OSM: Path = Path("services/osm/data/maps/denmark_filtered.osm")
BUILD_DIR: Path = Path("services/osm/data/build")
