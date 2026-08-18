from __future__ import annotations

import os
from pathlib import Path


# ==================================================
# Runtime configuration (deployment-level only)
# ==================================================

BUILD_DIR: Path = Path(
    os.getenv("OSM_SNAP_BUILD_DIR", "/data/build")
)

LAZY_TREES: bool = (
    os.getenv("OSM_SNAP_LAZY_TREES", "false").lower() == "true"
)
