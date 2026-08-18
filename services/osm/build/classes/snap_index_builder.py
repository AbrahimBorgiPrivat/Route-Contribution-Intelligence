from __future__ import annotations

import json
import logging
import math
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import osmium
from shapely.geometry import LineString
from shapely.strtree import STRtree
from tqdm import tqdm

from services.osm.build.config import ALLOWED_HIGHWAYS

# ==================================================
# Config
# ==================================================

@dataclass(frozen=True)
class SnapIndexConfig:
    """
    Configuration for the snap index build.

    input_crs:
        CRS of raw OSM coordinates (normally EPSG:4326).

    metric_crs:
        Projected CRS used for distance and geometry operations.
    """
    input_crs: str = "EPSG:4326"
    metric_crs: str = "EPSG:3857"


def _normalize_highway(hw: Any) -> Optional[str]:
    """
    Normalize OSM highway tag to a single string value.
    """
    if hw is None:
        return None
    if isinstance(hw, (list, tuple)):
        return str(hw[0]) if hw else None
    return str(hw)


# ==================================================
# OSM extraction
# ==================================================

class _WayGeometryExtractor(osmium.SimpleHandler):
    """
    OSM handler that extracts highway ways into raw geometries.

    Produces rows with:
      - osmid
      - highway
      - name
      - node_ids
      - geometry (LineString, lon/lat)
    """

    def __init__(self) -> None:
        super().__init__()
        self.rows: List[Dict[str, Any]] = []

    def way(self, w: osmium.osm.Way) -> None:
        """
        Called by osmium for each way in the file.
        """

        tags = {t.k: t.v for t in w.tags}
        hw = tags.get("highway")
        
        if hw is None:
            return
        
        if hw not in ALLOWED_HIGHWAYS:
            return

        coords: List[Tuple[float, float]] = []
        node_ids: List[int] = []

        for n in w.nodes:
            if not n.location.valid():
                continue
            node_ids.append(int(n.ref))
            coords.append((float(n.location.lon), float(n.location.lat)))

        if len(coords) < 2:
            return

        self.rows.append(
            {
                "osmid": int(w.id),
                "highway": _normalize_highway(w.tags.get("highway")),
                "name": w.tags.get("name"),
                "node_ids": node_ids,
                "geometry": LineString(coords),
            }
        )


# ==================================================
# Builder
# ==================================================

class OSMSnapIndexBuilder:
    """
    Builds a junction-bounded OSM snap index.

    Responsibilities:
    - Extract OSM highway geometries
    - Split ways into junction-bounded segments
    - Build spatial STRtrees
    - Build explicit turn objects with turn_id
    - Persist optimized runtime artifacts
    """

    def __init__(
        self,
        osm_xml_path: Path | str,
        out_dir: Path | str,
        cfg: SnapIndexConfig | None = None,
    ) -> None:
        """
        Parameters
        ----------
        osm_xml_path:
            Path to .osm or converted .osm.xml file.

        out_dir:
            Directory where build artifacts are written.

        cfg:
            Optional SnapIndexConfig override.
        """
        self.osm_xml_path = Path(osm_xml_path)
        self.out_dir = Path(out_dir)
        self.cfg = cfg or SnapIndexConfig()

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def build(self) -> None:
        """
        Execute the full snap-index build pipeline.

        This method is intended to be run offline and produces
        all artifacts required by the runtime snap service.
        """
        t0 = time.time()

        if not self.osm_xml_path.exists():
            raise FileNotFoundError(self.osm_xml_path)

        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "trees").mkdir(exist_ok=True)

        logging.info("=== BUILD OSM SNAP INDEX ===")
        logging.info("OSM XML : %s", self.osm_xml_path)
        logging.info("OUT DIR : %s", self.out_dir)

        ways = self._timed("Extract ways (WGS84)", self._extract_ways)
        node_degree = self._timed("Compute node usage", self._compute_node_degree, ways)

        segments = self._timed(
            "Split into junction-bounded segments",
            self._split_into_segments,
            ways,
            node_degree,
        )

        segments = self._timed(
            "Project segments to metric CRS",
            lambda s: s.to_crs(self.cfg.metric_crs),
            segments,
        )

        adjacency = self._timed(
            "Build adjacency (node → segments)",
            self._build_adjacency,
            segments,
        )

        trees, lookup = self._timed(
            "Build STRtrees per highway",
            self._build_trees,
            segments,
        )

        geom_by_id, meta_by_id = self._timed(
            "Build segment lookup dicts",
            self._build_segment_lookup,
            segments,
        )

        turns, turns_by_from = self._timed(
            "Compute turns (with turn_id)",
            self._compute_turns_with_ids,
            segments,
            meta_by_id,
            adjacency,
        )

        segment_id_by_row_index = segments["segment_id"].astype(int).tolist()

        self._timed(
            "Save artifacts",
            self._save,
            segments,
            trees,
            lookup,
            turns,
            turns_by_from,
            geom_by_id,
            meta_by_id,
            segment_id_by_row_index,
        )

        logging.info(
            "=== FINISHED (%.1fs) | segments=%d | turns=%d ===",
            time.time() - t0,
            len(segments),
            len(turns),
        )

    # --------------------------------------------------
    # Utilities
    # --------------------------------------------------

    def _timed(self, label: str, fn, *args):
        """
        Execute a function with timing and logging.
        """
        logging.info("%s …", label)
        t0 = time.time()
        out = fn(*args)
        logging.info("%s done (%.1fs)", label, time.time() - t0)
        return out

    # --------------------------------------------------
    # Build steps
    # --------------------------------------------------

    def _extract_ways(self) -> gpd.GeoDataFrame:
        """
        Extract raw OSM highway ways into a GeoDataFrame.
        """
        handler = _WayGeometryExtractor()
        handler.apply_file(str(self.osm_xml_path), locations=True)
        gdf = gpd.GeoDataFrame(
            handler.rows,
            geometry="geometry",
            crs=self.cfg.input_crs,
        )
        return gdf.reset_index(drop=True)

    def _compute_node_degree(self, ways: gpd.GeoDataFrame) -> Dict[int, int]:
        """
        Count how many ways use each node.
        """
        degree: Dict[int, int] = {}
        for nodes in ways["node_ids"]:
            for nid in set(nodes):
                degree[nid] = degree.get(nid, 0) + 1
        return degree

    def _split_into_segments(
        self,
        ways: gpd.GeoDataFrame,
        node_degree: Dict[int, int],
    ) -> gpd.GeoDataFrame:
        """
        Split ways into junction-bounded segments.
        """
        rows: List[Dict[str, Any]] = []
        sid = 1

        for _, r in tqdm(ways.iterrows(), total=len(ways), desc="Split ways"):
            nodes = r.node_ids
            coords = list(r.geometry.coords)

            def is_junction(i: int) -> bool:
                return i == 0 or i == len(nodes) - 1 or node_degree[nodes[i]] >= 2

            idxs = [i for i in range(len(nodes)) if is_junction(i)]

            for a, b in zip(idxs[:-1], idxs[1:]):
                rows.append(
                    {
                        "segment_id": sid,
                        "osmid": int(r.osmid),
                        "highway": r.highway,
                        "name": r.name,
                        "entry_node": int(nodes[a]),
                        "exit_node": int(nodes[b]),
                        "geometry": LineString(coords[a : b + 1]),
                    }
                )
                sid += 1

        return gpd.GeoDataFrame(rows, geometry="geometry", crs=ways.crs)

    def _build_adjacency(self, segments: gpd.GeoDataFrame) -> Dict[int, List[int]]:
        """
        Build node → segment adjacency map.
        """
        adjacency: Dict[int, List[int]] = {}
        for r in segments.itertuples(index=False):
            adjacency.setdefault(r.entry_node, []).append(r.segment_id)
            adjacency.setdefault(r.exit_node, []).append(r.segment_id)
        return adjacency

    # --------------------------------------------------
    # Turn computation
    # --------------------------------------------------

    def _compute_turns_with_ids(
        self,
        segments: gpd.GeoDataFrame,
        segment_meta: Dict[int, Dict[str, Any]],
        adjacency: Dict[int, List[int]],
    ) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, List[int]]]:
        """
        Compute explicit turn objects with unique turn_id.

        A turn represents:
        - a node
        - a from-segment
        - a to-segment
        - local in/out vectors (metric CRS)
        """
        seg = {r.segment_id: r for r in segments.itertuples(index=False)}
        meta = segment_meta

        def angle(v1_hat, v2_hat):
            if v1_hat is None or v2_hat is None:
                return None
            dot = v1_hat[0] * v2_hat[0] + v1_hat[1] * v2_hat[1]
            det = v1_hat[0] * v2_hat[1] - v1_hat[1] * v2_hat[0]
            return math.degrees(math.atan2(det, dot))

        turns: Dict[int, Dict[str, Any]] = {}
        turns_by_from: Dict[int, List[int]] = {}
        tid = 1

        for node, sids in tqdm(adjacency.items(), desc="Compute turns"):
            if len(sids) < 2:
                continue

            for from_sid in sids:
                from_seg = seg[from_sid]

                in_vec = meta[from_sid]["exit_tangent"]
                in_hat = meta[from_sid]["exit_tangent_hat"]

                for to_sid in sids:
                    if to_sid == from_sid:
                        continue

                    to_seg = seg[to_sid]

                    out_vec = meta[to_sid]["entry_tangent"]
                    out_hat = meta[to_sid]["entry_tangent_hat"]

                    ang = angle(in_hat, out_hat)

                    turns[tid] = {
                        "turn_id": tid,
                        "node": node,
                        "from_segment": from_sid,
                        "to_segment": to_sid,
                        "in_vector": in_vec,
                        "out_vector": out_vec,
                        "in_vector_hat": in_hat,
                        "out_vector_hat": out_hat,
                        "angle_deg": ang,
                        "from_osmid": from_seg.osmid,
                        "to_osmid": to_seg.osmid,
                        "from_highway": from_seg.highway,
                        "to_highway": to_seg.highway,
                    }
                    turns_by_from.setdefault(from_sid, []).append(tid)
                    tid += 1

        logging.info(
            "Computed %d turns (avg %.2f / segment)",
            len(turns),
            len(turns) / max(len(segments), 1),
        )

        return turns, turns_by_from

    # --------------------------------------------------
    # Trees & lookups
    # --------------------------------------------------

    def _build_trees(self, segments: gpd.GeoDataFrame):
        """
        Build STRtrees per highway class.
        """
        trees = {}
        lookup = {"metric_crs": str(segments.crs), "groups": {}}

        for hw in sorted(segments["highway"].dropna().unique()):
            subset = segments[segments["highway"] == hw]
            trees[hw] = STRtree(list(subset.geometry))
            lookup["groups"][hw] = {
                "row_index": subset.index.astype(int).tolist(),
                "n": len(subset),
            }
            logging.info("Indexed highway=%s (%d segments)", hw, len(subset))

        return trees, lookup

    def _build_segment_lookup(self, segments):
        """
        Build optimized runtime lookup dicts.

        In addition to base metadata, compute and store:
        - entry_tangent      (raw vector, INTO segment)
        - exit_tangent       (raw vector, INTO segment)
        - entry_tangent_hat  (unit vector)
        - exit_tangent_hat   (unit vector)

        All vectors are in the final metric CRS.
        """
        geom_by_id = {}
        meta_by_id = {}

        def _entry_tangent(coords):
            """
            Raw entry tangent: p1 - p0 (skip zero-length steps).
            """
            x0, y0 = coords[0]
            for i in range(1, len(coords)):
                x1, y1 = coords[i]
                dx = x1 - x0
                dy = y1 - y0
                if dx != 0.0 or dy != 0.0:
                    return dx, dy
            return None

        def _exit_tangent(coords):
            """
            Raw exit tangent INTO the segment: p_{n-1} - p_n.
            """
            xn, yn = coords[-1]
            for i in range(len(coords) - 2, -1, -1):
                xi, yi = coords[i]
                dx = xi - xn
                dy = yi - yn
                if dx != 0.0 or dy != 0.0:
                    return dx, dy
            return None

        def _unit(v):
            if v is None:
                return None
            dx, dy = v
            n = math.hypot(dx, dy)
            if n == 0.0:
                return None
            return dx / n, dy / n

        for r in segments.itertuples(index=False):
            geom_by_id[r.segment_id] = r.geometry

            meta = {
                "segment_id": r.segment_id,
                "osmid": r.osmid,
                "highway": r.highway,
                "name": r.name,
                "entry_node": r.entry_node,
                "exit_node": r.exit_node,
            }

            coords = list(r.geometry.coords)
            if len(coords) >= 2:
                entry_t = _entry_tangent(coords)
                exit_t = _exit_tangent(coords)

                meta.update(
                    {
                        "entry_tangent": entry_t,
                        "exit_tangent": exit_t,
                        "entry_tangent_hat": _unit(entry_t),
                        "exit_tangent_hat": _unit(exit_t),
                    }
                )
            else:
                meta.update(
                    {
                        "entry_tangent": None,
                        "exit_tangent": None,
                        "entry_tangent_hat": None,
                        "exit_tangent_hat": None,
                    }
                )

            meta_by_id[r.segment_id] = meta

        return geom_by_id, meta_by_id

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def _save(
        self,
        segments,
        trees,
        lookup,
        turns,
        turns_by_from,
        geom_by_id,
        meta_by_id,
        segment_id_by_row_index,
    ) -> None:
        """
        Persist all build artifacts to disk.
        """
        segments.to_parquet(self.out_dir / "segments.parquet")

        for hw, tree in trees.items():
            with open(self.out_dir / "trees" / f"{hw}.pkl", "wb") as f:
                pickle.dump(tree, f, protocol=pickle.HIGHEST_PROTOCOL)

        pickle.dump(geom_by_id, open(self.out_dir / "segment_geoms.pkl", "wb"))
        pickle.dump(meta_by_id, open(self.out_dir / "segment_meta.pkl", "wb"))
        pickle.dump(turns_by_from, open(self.out_dir / "turns_by_from_segment.pkl", "wb"))
        pickle.dump(segment_id_by_row_index,open(self.out_dir / "segment_id_by_row_index.pkl", "wb"))

        json.dump(turns, open(self.out_dir / "turns.json", "w"), indent=2)
        json.dump(lookup, open(self.out_dir / "segment_lookup.json", "w"), indent=2)
        json.dump(
            {
                "n_segments": len(segments),
                "n_turns": len(turns),
                "metric_crs": lookup["metric_crs"],
                "build_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            open(self.out_dir / "metadata.json", "w"),
            indent=2,
        )