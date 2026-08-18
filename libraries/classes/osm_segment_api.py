import os
from pyproj import Transformer
import requests
import math
from typing import List, Dict, Optional, Iterable, Set, Any, Literal
from tqdm import tqdm
from libraries.config import HIGHWAY_TYPES

# ==================================================
# Geometry helpers
# ==================================================

def rotate_unit_vector(
    v: tuple[float, float],
    angle_deg: float,
) -> tuple[float, float]:
    """
    Rotate a 2D unit vector by angle_deg degrees (CCW, unit-circle convention).
    """
    vx, vy = v
    theta = math.radians(angle_deg)
    c = math.cos(theta)
    s = math.sin(theta)
    return (
        vx * c - vy * s,
        vx * s + vy * c,
    )

# ==================================================
# Client
# ==================================================

class OSMSegmentClient:
    """
    Client for the OSM Snap Service (segment-level snapping).
    """
    DEFAULT_LOCAL_URL = "http://localhost:5010"
    DEFAULT_LOCAL_ENV_VAR = "OSM_SNAP_URL"
    MAX_BATCH_SIZE = 200
    def __init__(
        self,
        base_url: str = "local",
        input_crs: str = "EPSG:4326",
        output_crs: str = "EPSG:4326",
        allowed_highways: Optional[Iterable[HIGHWAY_TYPES]] = None,
        timeout: int = 30,
    ):
        self.base_url = (
            os.getenv(self.DEFAULT_LOCAL_ENV_VAR, self.DEFAULT_LOCAL_URL).rstrip("/")
            if base_url == "local"
            else base_url.rstrip("/")
        )
        self.input_crs = input_crs
        self.output_crs = output_crs
        self.metric_crs = "EPSG:25832"
        self._to_metric = Transformer.from_crs(self.output_crs, self.metric_crs, always_xy=True)
        self._from_metric = Transformer.from_crs(self.metric_crs, self.output_crs, always_xy=True)
        self.allowed_highways = allowed_highways
        self.timeout = timeout
    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------
    @staticmethod
    def _chunked(points: List, size: int) -> Iterable[List]:
        for i in range(0, len(points), size):
            yield points[i : i + size]
    
    def _to_metric_xy(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert lon/lat to metric CRS.

        Supports both pyproj.Transformer and test mocks.
        """
        if callable(self._to_metric):
            return self._to_metric(x, y)
        return self._to_metric.transform(x, y)

    def _from_metric_xy(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert metric CRS to output CRS.

        Supports both pyproj.Transformer and test mocks.
        """
        if callable(self._from_metric):
            return self._from_metric(x, y)
        return self._from_metric.transform(x, y)

    def _post(self, endpoint: str, payload: Dict) -> Dict:
        url = f"{self.base_url}{endpoint}"
        r = requests.post(url, json=payload, timeout=self.timeout)
        if not r.ok:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(
                f"OSM Snap Service error ({r.status_code})\n"
                f"Endpoint: {endpoint}\n"
                f"Response: {detail}"
            )
        return r.json()
    
    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def _snap_nearest_point(
        self,
        *,
        x: float,
        y: float,
    ) -> Dict[str, Any]:
        """
        Internal helper for calling /snap/nearest with client defaults.

        Parameters
        ----------
        x, y : float
            Coordinates in self.output_crs.

        Returns
        -------
        SnapNearestResponse as dict.
        """
        payload = {
            "x": x,
            "y": y,
            "input_crs": self.input_crs,
            "output_crs": self.output_crs,
        }
        if self.allowed_highways is not None:
            payload["allowed_highways"] = list(self.allowed_highways)
        return self._post("/snap/nearest", payload)

    def snap_nearest_batch(
            self,
            points: List[Dict[str, float]],
            *,
            x_key: str = "x",
            y_key: str = "y",
            show_progress: bool = True,
            chunk_size: int | None = None,
        ) -> List[Dict]:
            """
            Snap points in batches.

            chunk_size:
                If provided, points are processed in chunks of this size.
                This limits peak CPU and memory usage and avoids long blocking calls.
            """
            if not points:
                return []
            coord_pairs = [
                [float(p[x_key]), float(p[y_key])]
                for p in points
            ]
            if chunk_size is None:
                chunks = [coord_pairs]
            else:
                if chunk_size <= 0:
                    raise ValueError("chunk_size must be positive")
                chunks = list(self._chunked(coord_pairs, chunk_size))
            iterator = (
                tqdm(chunks, desc="OSM Snap chunks", leave=False)
                if show_progress
                else chunks
            )
            results: List[Dict] = []
            for chunk in iterator:
                payload = {
                    "points": chunk,
                    "input_crs": self.input_crs,
                    "output_crs": self.output_crs,
                }
                if self.allowed_highways is not None:
                    payload["allowed_highways"] = list(self.allowed_highways)
                response = self._post("/snap/nearest/batch", payload)
                batch_results = response.get("results")
                if not isinstance(batch_results, list):
                    raise RuntimeError(f"Unexpected response format: {response}")
                results.extend(batch_results)
            return results
    
    def fetch_segment(self, 
                      segment_id: int) -> Dict[str, Any]:
        params = {}
        if self.output_crs is not None:
            params["output_crs"] = self.output_crs

        r = requests.get(
            f"{self.base_url}/segments/{segment_id}",
            params=params,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()
    
    # --------------------------------------------------
    # Side-of-road endpoints from segment vectors
    # --------------------------------------------------

    def compute_side_endpoints_from_vectors(
        self,
        *,
        entry_lon: float,
        entry_lat: float,
        exit_lon: float,
        exit_lat: float,
        entry_tangent_hat: tuple[float, float],
        exit_tangent_hat: tuple[float, float],
        side: Literal["left", "right"],
        offset_m: float,
        entry_angle_deg: float = 90.0,
        exit_angle_deg: float = 90.0,
    ) -> tuple[dict, dict]:
        ex_m, ey_m = self._to_metric_xy(entry_lon, entry_lat)
        xx_m, xy_m = self._to_metric_xy(exit_lon, exit_lat)

        sign = +1.0 if side == "left" else -1.0

        entry_dir = rotate_unit_vector(entry_tangent_hat, sign * entry_angle_deg)
        exit_dir = rotate_unit_vector(exit_tangent_hat, sign * exit_angle_deg)

        entry_m = (ex_m + entry_dir[0] * offset_m, ey_m + entry_dir[1] * offset_m)
        exit_m = (xx_m + exit_dir[0] * offset_m, xy_m + exit_dir[1] * offset_m)

        start_lon, start_lat = self._from_metric_xy(*entry_m)
        end_lon, end_lat = self._from_metric_xy(*exit_m)

        return (
            {"lon": start_lon, "lat": start_lat},
            {"lon": end_lon, "lat": end_lat},
        )

    # --------------------------------------------------
    # Segment grouping
    # --------------------------------------------------
    def group_segments_on_side(
        self,
        seg: Dict[str, Any],
        *,
        allowed_highways: Iterable[HIGHWAY_TYPES] | None = None,
        side_of_road:  Literal["left", "right"] | None = None,
        use_rotated_side: bool = True,
        offset_m: float = 4.5,
        entry_angle_deg: float = 90.0,
        exit_angle_deg: float = 90.0,
    ) -> Dict[str, Any]:
        """
        Group connected segments along the same side of road,
        starting from a snap_nearest result.
        """
        if allowed_highways is None:
            allowed_highways = HIGHWAY_TYPES
        if side_of_road not in {"left", "right"} and side_of_road is not None:
            raise ValueError(f"Invalid side: {side_of_road} - should be left, right or None")
        if side_of_road is None:
            side_of_road = seg["geometry"].get("side_of_road")
        seg_seq_id = seg["segment"]["segment_id"]

        segments_seq: List[int] = [seg_seq_id]
        visited = {seg_seq_id}
        start_point = {
            "lon": seg["geometry"]["entry_point"]["x"],
            "lat": seg["geometry"]["entry_point"]["y"],
        }
        end_point = {
            "lon": seg["geometry"]["exit_point"]["x"],
            "lat": seg["geometry"]["exit_point"]["y"],
        }

        # --------------------------------------------------
        # Forward traversal
        # --------------------------------------------------
        last_seg = seg
        current = seg
        while True:
            turns = current["geometry"]["exit_point"].get("turns") or []
            candidates = [
                t for t in turns
                if t["from_segment"] == current["segment"]["segment_id"]
                and t["to_highway"] in set(allowed_highways)
                and t["to_segment"] not in visited
            ]
            if len(candidates) != 1:
                break
            t = candidates[0]
            if t["from_osmid"] != t["to_osmid"]:
                break

            next_seg = self.fetch_segment(t["to_segment"])
            last_seg = next_seg
            sid = next_seg["segment"]["segment_id"]
            segments_seq.append(sid)
            visited.add(sid)
            end_point = {
                "lon": next_seg["geometry"]["exit_point"]["x"],
                "lat": next_seg["geometry"]["exit_point"]["y"],
            }
            current = next_seg

        # --------------------------------------------------
        # Backward traversal
        # --------------------------------------------------
        first_seg = seg
        current = seg
        while True:
            turns = current["geometry"]["entry_point"].get("turns") or []
            candidates = [
                t for t in turns
                if t["from_segment"] == current["segment"]["segment_id"]
                and t["to_highway"] in set(allowed_highways)
                and t["to_segment"] not in visited
            ]
            if len(candidates) != 1:
                break
            t = candidates[0]
            if t["from_osmid"] != t["to_osmid"]:
                break

            prev_seg = self.fetch_segment(t["to_segment"])
            first_seg = prev_seg
            sid = prev_seg["segment"]["segment_id"]
            seg_seq_id = sid
            segments_seq.insert(0, sid)
            visited.add(sid)
            start_point = {
                "lon": prev_seg["geometry"]["entry_point"]["x"],
                "lat": prev_seg["geometry"]["entry_point"]["y"],
            }
            current = prev_seg

        # --------------------------------------------------
        # Side offset handling
        # --------------------------------------------------
        if use_rotated_side and side_of_road in {"left", "right"}:
            first_vectors = first_seg["geometry"]["vectors"]
            last_vectors = last_seg["geometry"]["vectors"]
        
            start_point, end_point = self.compute_side_endpoints_from_vectors(
                entry_lon=start_point["lon"],
                entry_lat=start_point["lat"],
                exit_lon=end_point["lon"],
                exit_lat=end_point["lat"],
                entry_tangent_hat=tuple(first_vectors["entry"]["tangent_hat"]),
                exit_tangent_hat=tuple(last_vectors["exit"]["tangent_hat"]),
                side=side_of_road,
                offset_m=offset_m,
                entry_angle_deg=entry_angle_deg,
                exit_angle_deg=exit_angle_deg,
            )

        segments_seq = [[sid, i] for i, sid in enumerate(segments_seq)]

        return {
            "seg_seq_id": seg_seq_id,
            "site_of_road": side_of_road,
            "visited_segments": visited,
            "segments": segments_seq,
            "start_point": start_point,
            "end_point": end_point,
        }
