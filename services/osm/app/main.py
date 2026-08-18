from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import BUILD_DIR, LAZY_TREES
from app.runtime.loader import OSMSnapIndexLoader
from app.runtime.index import OSMSnapIndex
from app.service.server import router
from app.runtime.errors import register_osm_error_handlers

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)

# --------------------------------------------------
# Application lifespan
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Responsibilities:
      - Load the OSM snap index ONCE at startup
      - Store it on app.state for dependency injection
      - Keep it alive for the full lifetime of the service
    """
    logging.info("Starting OSM Snap Service")
    logging.info("Build dir      : %s", BUILD_DIR)
    logging.info("Lazy STRtrees  : %s", LAZY_TREES)

    loader = OSMSnapIndexLoader(
        build_dir=BUILD_DIR,
        lazy_trees=LAZY_TREES,
    )

    state = loader.load()
    app.state.snap_index = OSMSnapIndex(state)

    logging.info("OSM Snap Service ready")
    yield
    logging.info("Shutting down OSM Snap Service")


# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(
    title="OSM Snap Service",
    version="0.1.0",
    lifespan=lifespan,
)

register_osm_error_handlers(app)
app.include_router(router)