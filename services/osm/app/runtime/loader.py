from __future__ import annotations

import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict

from app.runtime.types import SnapIndexState


class OSMSnapIndexLoader:
    """
    Load runtime artifacts produced by OSMSnapIndexBuilder.

    Expected build_dir structure
    ----------------------------
    build_dir/
      segment_geoms.pkl
      segment_meta.pkl
      segment_id_by_row_index.pkl
      turns_by_from_segment.pkl
      turns.json
      segment_lookup.json
      metadata.json
      trees/
        <highway>.pkl

    Key correctness constraint
    --------------------------
    STRtrees are built per-highway on subsets of the global segments table.
    Therefore, we MUST load segment_lookup.json and reconstruct:
        row_index_by_highway[hw] = global_row_indices used by that tree
    to map STRtree local indices back to the global segment_id list.
    """

    def __init__(self, build_dir: str | Path, *, lazy_trees: bool = False) -> None:
        self.build_dir = Path(build_dir)
        self.lazy_trees = bool(lazy_trees)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def load(self) -> SnapIndexState:
        """
        Load all runtime artifacts into memory and assemble SnapIndexState.
        """
        t0 = time.perf_counter()
        logging.info(
            "Loading OSM snap index (build_dir=%s, lazy_trees=%s)",
            self.build_dir,
            self.lazy_trees,
        )
        if not self.build_dir.exists():
            raise FileNotFoundError(self.build_dir)

        # ------------------------------
        # Core segment artifacts
        # ------------------------------
        geom_by_id = self._load_pickle("segment_geoms.pkl")
        logging.info("Loaded segment_geoms.pkl (%d)", len(geom_by_id))

        meta_by_id = self._load_pickle("segment_meta.pkl")
        logging.info("Loaded segment_meta.pkl (%d)", len(meta_by_id))

        segment_id_by_row_index = self._load_pickle("segment_id_by_row_index.pkl")
        logging.info("Loaded segment_id_by_row_index.pkl (%d)", len(segment_id_by_row_index))

        # ------------------------------
        # Turns
        # ------------------------------
        turns_raw = self._load_json("turns.json")
        turns: Dict[int, Dict[str, Any]] = {}
        for k, v in turns_raw.items():
            turns[int(k)] = v
        logging.info("Loaded turns.json (%d)", len(turns))

        turns_by_from = self._load_pickle("turns_by_from_segment.pkl")
        logging.info("Loaded turns_by_from_segment.pkl (%d)", len(turns_by_from))

        # ------------------------------
        # Lookup (needed for row_index_by_highway)
        # ------------------------------
        lookup = self._load_json("segment_lookup.json")
        logging.info("Loaded segment_lookup.json")

        groups = lookup.get("groups", {}) or {}
        row_index_by_highway: Dict[str, list[int]] = {
            str(hw): list(map(int, info.get("row_index", [])))
            for hw, info in groups.items()
        }
        logging.info("Loaded highway groups: %d", len(row_index_by_highway))

        # ------------------------------
        # Metadata
        # ------------------------------
        metadata = self._load_json("metadata.json")
        metric_crs = metadata.get("metric_crs")
        if metric_crs is None:
            raise ValueError("metadata.json missing 'metric_crs'")

        # ------------------------------
        # Trees
        # ------------------------------
        trees_dir = self.build_dir / "trees"
        if not trees_dir.exists():
            raise FileNotFoundError(trees_dir)
        trees: Dict[str, Any] = {}
        tree_paths = sorted(trees_dir.glob("*.pkl"))
        if self.lazy_trees:
            logging.info("STRtrees will be loaded lazily")
            for p in tree_paths:
                trees[p.stem] = None
            tree_loader = self._make_tree_loader(trees_dir, trees)
        else:
            for p in tree_paths:
                trees[p.stem] = self._load_pickle_path(p)
            logging.info("Loaded STRtrees for %d highway types", len(trees))
            tree_loader = None
        state = SnapIndexState(
            metric_crs=str(metric_crs),
            geom_by_segment_id=geom_by_id,
            meta_by_segment_id=meta_by_id,
            row_index_by_highway=row_index_by_highway,
            segment_id_by_row_index=list(map(int, segment_id_by_row_index)),
            turns=turns,
            turns_by_from_segment={int(k): list(map(int, v)) for k, v in turns_by_from.items()},
            trees=trees,
            tree_loader=tree_loader,
        )
        logging.info("OSM snap index loaded successfully (%.1f ms)", (time.perf_counter() - t0) * 1000)
        return state

    # --------------------------------------------------
    # Lazy tree loader
    # --------------------------------------------------

    def _make_tree_loader(self, trees_dir: Path, trees: Dict[str, Any]):
        """
        Create a closure that loads a single STRtree into the provided dict.
        """
        loaded: set[str] = set()

        def _loader(highway: str) -> None:
            if highway in loaded:
                return
            p = trees_dir / f"{highway}.pkl"
            if not p.exists():
                loaded.add(highway)
                return
            t0 = time.perf_counter()
            with open(p, "rb") as f:
                trees[highway] = pickle.load(f)
            loaded.add(highway)
            logging.info("Loaded STRtree lazily: %s (%.1f ms)", highway, (time.perf_counter() - t0) * 1000)
        return _loader

    # --------------------------------------------------
    # File helpers
    # --------------------------------------------------

    def _load_pickle(self, filename: str) -> Any:
        path = self.build_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, "rb") as f:
            return pickle.load(f)

    def _load_pickle_path(self, path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, "rb") as f:
            return pickle.load(f)

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.build_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
