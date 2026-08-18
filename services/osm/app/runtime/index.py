from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, Set, Tuple, List, Sequence
from shapely.geometry import Point
from pyproj import CRS, Transformer

 
from app.runtime.types import SnapIndexState
from app.runtime.errors import InvalidHighwayFilterError, NoSegmentFoundError, InvalidCRSError

class OSMSnapIndex:
    """
    Runtime snap index API (simple version).

    Provides:
      - snap_nearest: nearest segment lookup with correct STRtree index mapping
      - get_turn: lookup a single turn by turn_id
      - get_turns_from_segment: outgoing turns from a segment (resolved dicts)

    Important
    ---------
    Segment geometries and STRtrees are in state.metric_crs.
    The user may pass input points in any CRS (input_crs), and request
    output in another CRS (output_crs).
    """

    def __init__(self, state: SnapIndexState) -> None:
        self.state = state
        self._metric_crs = CRS.from_user_input(state.metric_crs)
        self._transformers: Dict[tuple[str, str], Transformer] = {}
    
    # ==================================================
    # CRS validation
    # ==================================================

    def _validate_crs(self, crs: str) -> None:
        try:
            CRS.from_user_input(crs)
        except Exception:
            raise InvalidCRSError(crs)

    def _get_transformer(self, src: str, dst: str) -> Transformer:
        key = (src, dst)
        if key not in self._transformers:
            self._transformers[key] = Transformer.from_crs(
                CRS.from_user_input(src),
                CRS.from_user_input(dst),
                always_xy=True,
            )
        return self._transformers[key]

    def _to_metric(self, x: float, y: float, input_crs: str) -> tuple[float, float]:
        if input_crs == self.state.metric_crs:
            return x, y
        t = self._get_transformer(input_crs, self.state.metric_crs)
        return t.transform(x, y)

    def _from_metric(self, x: float, y: float, output_crs: str) -> tuple[float, float]:
        if output_crs == self.state.metric_crs:
            return x, y
        t = self._get_transformer(self.state.metric_crs, output_crs)
        return t.transform(x, y)

    # ==================================================
    # Geometry helpers
    # ==================================================

    @staticmethod
    def _classify_side(entry: Point, exit_: Point, proj: Point) -> str:
        """
        Classify projected point as being left/right/center relative to
        the directed segment (entry -> exit) in metric CRS.
        """
        ax, ay = entry.x, entry.y
        bx, by = exit_.x, exit_.y
        px, py = proj.x, proj.y

        vx, vy = bx - ax, by - ay
        wx, wy = px - ax, py - ay

        cross = vx * wy - vy * wx
        if abs(cross) < 1e-9:
            return "center"
        return "left" if cross > 0 else "right"
    
    def _turns_at_node(self, node_id: int) -> List[Dict[str, Any]]:
        """
        Return all turns that occur at a given node, keyed by turn_id.
        """
        out: Dict[int, Dict[str, Any]] = {}
        for tid, t in self.state.turns.items():
            if int(t.get("node")) == int(node_id):
                out[tid] = t
        return list(out.values())
    
    # --------------------------------------------------
    # Core snapping worker (metric CRS only)
    # --------------------------------------------------

    def _snap_metric_point(
        self,
        *,
        x_m: float,
        y_m: float,
        output_crs: str,
        allowed_highways: Optional[Iterable[str]],
    ) -> Dict[str, Any]:
        p = Point(x_m, y_m)
        if allowed_highways is not None:
            unknown = set(allowed_highways) - set(self.state.trees.keys())
            if unknown:
                raise InvalidHighwayFilterError(sorted(unknown))
            highways = allowed_highways
        else:
            highways = self.state.trees.keys()
        best_sid = None
        best_proj = None
        best_dist = float("inf")
        for hw in highways:
            tree = self.state.get_tree(hw)
            if tree is None:
                continue

            hit = tree.nearest(p)
            if hit is None:
                continue
            hits = [hit]

            row_map = self.state.row_index_by_highway.get(hw)
            if not row_map:
                continue

            for local_idx in hits:
                local_idx = int(local_idx)
                if local_idx >= len(row_map):
                    continue

                row_idx = row_map[local_idx]
                if row_idx >= len(self.state.segment_id_by_row_index):
                    continue

                sid = self.state.segment_id_by_row_index[row_idx]
                geom = self.state.geom_by_segment_id.get(sid)
                if geom is None:
                    continue

                proj_d = geom.project(p)
                proj_pt = geom.interpolate(proj_d)
                dist = p.distance(proj_pt)

                if dist < best_dist:
                    best_dist = dist
                    best_sid = sid
                    best_proj = proj_pt

        if best_sid is None or best_proj is None:
            raise NoSegmentFoundError(hint="No candidate segments in search radius.")

        geom = self.state.geom_by_segment_id[best_sid]
        meta = self.state.meta_by_segment_id[best_sid]

        entry_node = int(meta["entry_node"])
        exit_node = int(meta["exit_node"])
        entry_turns = []
        exit_turns = []

        for tid in self.state.turns_by_from_segment.get(int(best_sid), []):
            t = self.state.turns.get(tid)
            if t is None:
                continue
            n = int(t.get("node"))
            if n == entry_node:
                entry_turns.append(t)
            elif n == exit_node:
                exit_turns.append(t)

        entry_pt = Point(geom.coords[0])
        exit_pt = Point(geom.coords[-1])

        side = self._classify_side(entry_pt, exit_pt, best_proj)

        ex, ey = self._from_metric(entry_pt.x, entry_pt.y, output_crs)
        xx, xy = self._from_metric(exit_pt.x, exit_pt.y, output_crs)
        px, py = self._from_metric(best_proj.x, best_proj.y, output_crs)
        
        geometry = {
            "entry_point": {"x": ex, "y": ey, "node_id": entry_node, "turns": entry_turns or None},
            "exit_point": {"x": xx, "y": xy, "node_id": exit_node, "turns": exit_turns or None},
            "side_of_road": side,
            "vectors": {
                "entry": {"tangent": meta.get("entry_tangent"), "tangent_hat": meta.get("entry_tangent_hat")},
                "exit": {"tangent": meta.get("exit_tangent"), "tangent_hat": meta.get("exit_tangent_hat")},
            },
            "crs": output_crs,
        }

        return {
            "segment": meta,
            "projected_point": {"x": px, "y": py, "crs": output_crs},
            "geometry": geometry,
        }
    # --------------------------------------------------
    # Public API: snap_nearest
    # --------------------------------------------------

    def snap_nearest(
        self,
        *,
        x: float,
        y: float,
        input_crs: str,
        output_crs: Optional[str] = None,
        allowed_highways: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Snap a point to the nearest road segment.

        ----------
        Parameters
        ----------
          - x, y:
              Input coordinate in input_crs.
          - input_crs:
              CRS of the input point.
          - output_crs:
              CRS of returned geometry and projected point.
              Defaults to the index metric CRS if None.
          - allowed_highways:
              Restrict search to these highway tags (must exist in index).
              If None, all indexed highway classes are used.

        ----------
        Returns
        ----------
          - input:
              Original input coordinate and CRS.
          - segment:
              Segment metadata dictionary.
          - projected_point:
              Orthogonal projection of the input point onto the segment geometry,
              expressed in output_crs.
          - geometry:
              Dictionary containing:
                - entry_point:
                    Segment entry point (x, y, node_id, turns).
                - exit_point:
                    Segment exit point (x, y, node_id, turns).
                - side_of_road:
                    Classified side of road (left / right / center / None).
                - vectors:
                    Precomputed local segment vectors:
                      - entry: raw tangent and unit tangent at segment entry.
                      - exit: raw tangent and unit tangent at segment exit.
                - crs:
                    CRS of all geometry coordinates.
    """    
    

        self._validate_crs(input_crs)
        if output_crs is None:
            output_crs = self.state.metric_crs
        self._validate_crs(output_crs)

        x_m, y_m = self._to_metric(x, y, input_crs)

        snap = self._snap_metric_point(
            x_m=x_m,
            y_m=y_m,
            output_crs=output_crs,
            allowed_highways=allowed_highways,
        )

        snap["input"] = {"x": x, "y": y, "crs": input_crs}
        return snap

    # --------------------------------------------------
    # Public API: snap_nearest_batch 
    # --------------------------------------------------

    def snap_nearest_batch(
        self,
        points: Sequence[Sequence[float]],
        *,
        input_crs: str,
        output_crs: Optional[str] = None,
        allowed_highways: Optional[Iterable[str]] = None,
        strict: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Snap multiple points to their nearest road segments.

        This is a high-performance batch variant of snap_nearest.
        All points are transformed and snapped using a shared spatial index,
        avoiding repeated per-point setup and index construction.

        ----------
        Parameters
        ----------
          - points:
              Sequence of [x, y] coordinate pairs.
              Example: [[x1, y1], [x2, y2], ...]
          - input_crs:
              CRS of all input points.
          - output_crs:
              CRS of returned geometry and projected points.
              Defaults to the index metric CRS if None.
          - allowed_highways:
              Restrict snapping to these highway tags (must exist in index).
              If None, all indexed highway classes are used.
          - strict:
              Error handling mode:
                - True  → raise on first invalid point or snap failure.
                - False → return a result entry with an error field for failures.

        ----------
        Returns
        ----------
          A list of snap results aligned 1:1 with the input points.
          Each entry has the same structure as snap_nearest, containing:
            - input
            - segment
            - projected_point
            - geometry

          If strict=False, failed points yield an entry with:
            - input
            - error
        """

        self._validate_crs(input_crs)
        if output_crs is None:
            output_crs = self.state.metric_crs
        self._validate_crs(output_crs)

        if not isinstance(points, (list, tuple)):
            raise TypeError("points must be a sequence of [x, y] pairs")
        
        MAX_BATCH_SIZE = 250
        if len(points) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch too large: Maximum number of entries {MAX_BATCH_SIZE}")

        # --------------------------------------------------
        # 1. Transform ALL points once
        # --------------------------------------------------
        metric_points: List[Tuple[float, float]] = []
        for i, pt in enumerate(points):
            if (
                not isinstance(pt, (list, tuple))
                or len(pt) != 2
                or not all(isinstance(v, (int, float)) for v in pt)
            ):
                if strict:
                    raise ValueError(f"Invalid point at index {i}: {pt}")
                metric_points.append(None)
                continue
            metric_points.append(self._to_metric(pt[0], pt[1], input_crs))

        # --------------------------------------------------
        # 2. Snap each metric point (NO CRS / index rebuild)
        # --------------------------------------------------
        results: List[Dict[str, Any]] = []
        for i, mp in enumerate(metric_points):
            if mp is None:
                results.append(None)
                continue
            try:
                snap = self._snap_metric_point(
                    x_m=mp[0],
                    y_m=mp[1],
                    output_crs=output_crs,
                    allowed_highways=allowed_highways,
                )
                snap["input"] = {
                    "x": points[i][0],
                    "y": points[i][1],
                    "crs": input_crs,
                }
                results.append(snap)

            except Exception as e:
                if strict:
                    raise
                results.append(
                    {
                        "input": {
                            "x": points[i][0],
                            "y": points[i][1],
                            "crs": input_crs,
                        },
                        "error": str(e),
                    }
                )
        return results
    
    def get_segment(
        self,
        *,
        segment_id: int,
        output_crs: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return segment metadata and geometry endpoints.

        ----------
        Parameters
        ----------
        segment_id : Unique identifier of the road segment.
        output_crs : CRS of returned geometry. If None, the service metric CRS is used.

        -------
        Returns
        -------
        - segment : Segment metadata (id, nodes, highway type, etc.).
        - geometry : Geometry information in output_crs, including:
        - entry_point : Segment entry points. 
        - exit_point : Segment exit points. 
        - crs : output_crs
        """
        if segment_id not in self.state.geom_by_segment_id:
            raise KeyError(f"Segment {segment_id} not found")

        if output_crs is None:
            output_crs = self.state.metric_crs
        self._validate_crs(output_crs)

        geom = self.state.geom_by_segment_id[segment_id]
        meta = self.state.meta_by_segment_id[segment_id]

        entry = Point(geom.coords[0])
        exit_ = Point(geom.coords[-1])

        ex, ey = self._from_metric(entry.x, entry.y, output_crs)
        xx, xy = self._from_metric(exit_.x, exit_.y, output_crs)
        entry_turns = []
        exit_turns = []

        for tid in self.state.turns_by_from_segment.get(segment_id, []):
            t = self.state.turns.get(tid)
            if t is None:
                continue
            if t.get("node") == meta["entry_node"]:
                entry_turns.append(t)
            elif t.get("node") == meta["exit_node"]:
                exit_turns.append(t)

        geometry = {
            "entry_point": {
                "x": ex,
                "y": ey,
                "node_id": meta["entry_node"],
                "turns": entry_turns or None,
            },
            "exit_point": {
                "x": xx,
                "y": xy,
                "node_id": meta["exit_node"],
                "turns": exit_turns or None,
            },
            "vectors": {
                "entry": {
                    "tangent": meta.get("entry_tangent"),
                    "tangent_hat": meta.get("entry_tangent_hat"),
                },
                "exit": {
                    "tangent": meta.get("exit_tangent"),
                    "tangent_hat": meta.get("exit_tangent_hat"),
                },
            },
            "crs": output_crs,
        }

        return {
            "segment": meta,
            "geometry": geometry,
        }

    def get_turn(self, turn_id: int) -> Optional[Dict[str, Any]]:
        """
        Return a single turn by turn_id.
        """
        return self.state.turns.get(int(turn_id))
    
    def get_turns_from_node(self, node_id: int) -> list[Dict[str, Any]]:
        """
        Return all turns that occur at a given node.
        """
        nid = int(node_id)
        return [
            t for t in self.state.turns.values()
            if int(t.get("node")) == nid
        ]

    def get_turns_from_segment(self, segment_id: int) -> list[Dict[str, Any]]:
        """
        Return all outgoing turns from a segment as full turn dicts.
        """
        tids = self.state.turns_by_from_segment.get(int(segment_id), [])
        return [self.state.turns[tid] for tid in tids if tid in self.state.turns]
