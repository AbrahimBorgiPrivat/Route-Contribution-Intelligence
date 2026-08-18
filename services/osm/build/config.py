from __future__ import annotations

from typing import Set

# ==================================================
# Highway profiles (BUILD-TIME ONLY)
# ==================================================
CAR_HIGHWAYS: Set[str] = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "service",
    "living_street",
}
PATH_HIGHWAYS: Set[str] = {
    "footway",
    "path",
    "cycleway",
    "bridleway",
    "steps",
    "track",
}
ALLOWED_HIGHWAYS: Set[str] = CAR_HIGHWAYS
