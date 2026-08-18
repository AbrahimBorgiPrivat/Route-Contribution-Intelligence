from __future__ import annotations

import logging
from services.osm.build.classes.osm_highway_extractor import (
    OSMHighwayExtractor,
    HighwayFilterConfig,
)
from services.osm.build.classes.snap_index_builder import (
    OSMSnapIndexBuilder,
    SnapIndexConfig,
)
from services.osm.build.paths import (
    OSM_PBF,
    FILTERED_OSM,
    BUILD_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)

# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main() -> None:
    logging.info("=== BUILD OSM SNAP INDEX ===")

    # --------------------------------------------------
    # Step 1/2: Extract highway-only OSM from PBF
    # --------------------------------------------------
    logging.info("Step 1/2: Extracting highway subgraph from PBF")

    filter_cfg = HighwayFilterConfig()
    extractor = OSMHighwayExtractor(cfg=filter_cfg)

    filtered_osm_path = extractor.extract(
        osm_input_path=OSM_PBF,
        osm_output_path=FILTERED_OSM,
    )

    logging.info(f"Filtered OSM ready: {filtered_osm_path}")

    # --------------------------------------------------
    # Step 2/2: Build snap index from filtered OSM
    # --------------------------------------------------
    logging.info("Step 2/2: Building snap index")

    snap_cfg = SnapIndexConfig(
        input_crs="EPSG:4326",
        metric_crs="EPSG:3857",
    )

    builder = OSMSnapIndexBuilder(
        osm_xml_path=filtered_osm_path,
        out_dir=BUILD_DIR,
        cfg=snap_cfg,
    )

    builder.build()

    logging.info("=== OSM SNAP INDEX BUILD FINISHED ===")


if __name__ == "__main__":
    main()

