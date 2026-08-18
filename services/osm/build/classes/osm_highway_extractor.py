from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

import osmium
from tqdm import tqdm

from services.osm.build.config import ALLOWED_HIGHWAYS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)

@dataclass(frozen=True)
class HighwayFilterConfig:
    allowed_highways: Set[str] = None  # type: ignore[assignment]
    keep_ways_without_highway: bool = False  # normally False

    def __post_init__(self):
        if self.allowed_highways is None:
            object.__setattr__(self, "allowed_highways", set(ALLOWED_HIGHWAYS))


class _WayCollector(osmium.SimpleHandler):
    """
    First pass: collect kept way ids + all node refs used by kept ways.
    """
    def __init__(self, cfg: HighwayFilterConfig):
        super().__init__()
        self.cfg = cfg
        self.kept_way_ids: Set[int] = set()
        self.node_refs: Set[int] = set()
        self._pbar = None

    def set_progress_bar(self, pbar):
        self._pbar = pbar

    def way(self, w: osmium.osm.Way) -> None:
        if self._pbar is not None:
            self._pbar.update(1)

        tags = {t.k: t.v for t in w.tags}
        hw = tags.get("highway")

        if hw is None and not self.cfg.keep_ways_without_highway:
            return

        if hw is not None and hw not in self.cfg.allowed_highways:
            return

        self.kept_way_ids.add(w.id)
        for n in w.nodes:
            self.node_refs.add(n.ref)


class _OSMWriter(osmium.SimpleHandler):
    """
    Second pass: write nodes (only those referenced) + ways (only kept).
    """
    def __init__(
        self,
        out_path: Path,
        kept_way_ids: Set[int],
        kept_node_refs: Set[int],
    ):
        super().__init__()
        self.out_path = out_path
        self.kept_way_ids = kept_way_ids
        self.kept_node_refs = kept_node_refs

        self._writer = osmium.SimpleWriter(str(out_path))
        self._pbar_nodes = None
        self._pbar_ways = None

    def close(self) -> None:
        self._writer.close()

    def set_progress_bars(self, pbar_nodes, pbar_ways) -> None:
        self._pbar_nodes = pbar_nodes
        self._pbar_ways = pbar_ways

    def node(self, n: osmium.osm.Node) -> None:
        if self._pbar_nodes is not None:
            self._pbar_nodes.update(1)

        if n.id in self.kept_node_refs:
            self._writer.add_node(n)

    def way(self, w: osmium.osm.Way) -> None:
        if self._pbar_ways is not None:
            self._pbar_ways.update(1)

        if w.id in self.kept_way_ids:
            self._writer.add_way(w)


class OSMHighwayExtractor:
    """
    Stream-filter an OSM PBF/XML to a smaller .osm (XML) containing:
    - ways with highway in allowed_highways
    - all nodes referenced by those ways

    This guarantees no missing-node references for retained ways.
    """

    def __init__(self, cfg: Optional[HighwayFilterConfig] = None):
        self.cfg = cfg or HighwayFilterConfig()

    def extract(self, osm_input_path: str | Path, osm_output_path: str | Path) -> Path:
        osm_input_path = Path(osm_input_path)
        osm_output_path = Path(osm_output_path)
        osm_output_path.parent.mkdir(parents=True, exist_ok=True)

        logging.info("=== HighwayFilter: pass 1/2 (collect ways + node refs) ===")
        collector = _WayCollector(self.cfg)

        with tqdm(desc="Scan ways", unit="way") as pbar:
            collector.set_progress_bar(pbar)
            collector.apply_file(str(osm_input_path), locations=False)

        logging.info(f"Kept ways: {len(collector.kept_way_ids):,}")
        logging.info(f"Referenced nodes: {len(collector.node_refs):,}")

        logging.info("=== HighwayFilter: pass 2/2 (write filtered .osm) ===")
        writer = _OSMWriter(
            out_path=osm_output_path,
            kept_way_ids=collector.kept_way_ids,
            kept_node_refs=collector.node_refs,
        )

        with tqdm(desc="Write nodes", unit="node") as pbar_nodes, tqdm(desc="Write ways", unit="way") as pbar_ways:
            writer.set_progress_bars(pbar_nodes, pbar_ways)
            writer.apply_file(str(osm_input_path), locations=False)
            writer.close()

        logging.info(f"Filtered OSM written to: {osm_output_path}")
        return osm_output_path
