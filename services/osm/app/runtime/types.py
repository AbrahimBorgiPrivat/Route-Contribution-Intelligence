from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class SnapIndexState:
    """
    Immutable runtime state for OSMSnapIndex.

    Notes
    -----
    - Segment geometries are in metric_crs.
    - STRtrees are built per highway class, so we MUST maintain:
        (highway-tree local index) -> (global row index) -> (segment_id)
      via row_index_by_highway + segment_id_by_row_index.
    - turns are stored as:
        turns: turn_id -> turn dict
        turns_by_from_segment: from_segment -> [turn_id, ...]
    """
    metric_crs: str
    geom_by_segment_id: Dict[int, Any]
    meta_by_segment_id: Dict[int, Dict[str, Any]]
    row_index_by_highway: Dict[str, List[int]]      
    segment_id_by_row_index: List[int]              
    turns: Dict[int, Dict[str, Any]]                
    turns_by_from_segment: Dict[int, List[int]]     
    trees: Dict[str, Any]                           
    tree_loader: Optional[Any] = None

    def get_tree(self, highway: str):
        """
        Return STRtree for a highway class. If lazy loading is enabled, load on demand.
        """
        t = self.trees.get(highway)
        if t is not None:
            return t
        if self.tree_loader is not None and highway in self.trees:
            self.tree_loader(highway)
            return self.trees.get(highway)
        return None
