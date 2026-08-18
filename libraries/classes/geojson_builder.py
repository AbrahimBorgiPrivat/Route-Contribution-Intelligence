import os
import json
from typing import List, Dict, Any, Optional
import polyline

class GeoJSONBuilder:
    """
    Builder class that creates:
        - <route_id>_markers.geojson
        - <route_id>_route.geojson
        - <route_id>.json (index)
    """

    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Utility: OSRM step decoder
    # ------------------------------------------------------------------
    @staticmethod
    def _decode_osrm_steps(legs) -> List[List[float]]:
        """
        OSRM legs are lists of steps, where each step has a 'geometry'.

        Structure:
            legs = [
                [ {geometry}, {geometry}, ... ],
                [ {geometry}, {geometry}, ... ],
                ...
            ]
        """
        coords: List[List[float]] = []
        for step_list in legs:  
            for step in step_list:
                geom = step.get("geometry")
                if geom:
                    pts = polyline.decode(geom)  
                    coords.extend([[lon, lat] for lat, lon in pts])
        return coords

    # ------------------------------------------------------------------
    # Utility: frozenset → string for dict keys
    # ------------------------------------------------------------------
    @staticmethod
    def _fs_to_str(fs) -> str:
        """
        Convert frozenset({6}) -> "{6}"
        Convert frozenset({6, 9}) -> "{6,9}"
        """
        from collections.abc import Set as AbstractSet
        if isinstance(fs, AbstractSet):
            return "{" + ",".join(str(x) for x in sorted(fs)) + "}"
        return str(fs)

    # ------------------------------------------------------------------
    # Utility: recursively convert to JSON-safe objects
    # ------------------------------------------------------------------
    @classmethod
    def _json_safe(cls, obj):
        """
        Recursively convert:
          - frozenset / set -> list (for values) or "{...}" string (for keys)
          - numpy integer / float -> Python int / float
          - tuples -> lists
        So the result is always JSON serializable.
        """
        # Late import to avoid hard dependency if numpy isn't installed
        try:
            import numpy as np
        except ImportError:
            np = None
        # Sets as values → list
        from collections.abc import Set as AbstractSet
        if isinstance(obj, AbstractSet):
            # For values (not keys) we represent as sorted list
            return [cls._json_safe(x) for x in sorted(obj)]
        # Dict → clean keys and values
        if isinstance(obj, dict):
            clean_dict = {}
            for k, v in obj.items():
                # Keys: if they are set-like, use "{6,9}" style
                if isinstance(k, AbstractSet):
                    key = cls._fs_to_str(k)
                else:
                    key = str(k)
                clean_dict[key] = cls._json_safe(v)
            return clean_dict
        # Lists / tuples → clean each element
        if isinstance(obj, (list, tuple)):
            return [cls._json_safe(v) for v in obj]
        # Numpy numeric types → native Python
        if np is not None:
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
        # Everything else → return as is
        return obj

    # ------------------------------------------------------------------
    # MARKERS GEOJSON
    # ------------------------------------------------------------------
    def build_markers_geojson(
        self,
        route_id: str,
        locations: List[Dict[str, Any]],
        t1_normal: List[int],
        t1_outlier: List[int],
        t1_sig: List[int],
        t2_normal: List[int],
        t2_outlier: List[int],
        t2_sig: List[int],
        marker_meta: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> str:
        """
        Writes <route_id>_markers.geojson.
        """
        features: List[Dict[str, Any]] = []
        marker_meta = marker_meta or {}
        def add_marker(idx: int, layer: str, label: str):
            loc = locations[idx]
            props = {
                "label": label,
                "layer": layer,
                "number": idx,
                "route_id": str(route_id),
            }
            extra = marker_meta.get(idx)
            if extra:
                props.update(extra)
            features.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(loc["lon"]),
                            float(loc["lat"]),
                        ],
                    },
                }
            )
        for i in t1_normal:
            add_marker(i, "T1 Normal", "T1 Normal")
        for i in t1_outlier:
            add_marker(i, "T1 Outlier", "T1 Outlier")
        for i in t1_sig:
            add_marker(i, "T1 Significant", "T1 Significant")
        for i in t2_normal:
            add_marker(i, "T2 Normal", "T2 Normal")
        for i in t2_outlier:
            add_marker(i, "T2 Outlier", "T2 Outlier")
        for i in t2_sig:
            add_marker(i, "T2 Significant", "T2 Significant")
        fc = {"type": "FeatureCollection", "features": features}
        filepath = os.path.join(self.save_dir, f"{route_id}_markers.geojson")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2, ensure_ascii=False)
        return filepath

    # ------------------------------------------------------------------
    # ROUTE GEOJSON
    # ------------------------------------------------------------------
    def build_route_geojson(
        self,
        route_id: str,
        route_features: List[Dict[str, Any]],
    ) -> str:
        """
        route_features: list of dicts with:
            {
              "layer": "T1 Original",
              "steps_list": <OSRM return>,
            }
        Writes <route_id>_route.geojson
        """
        features: List[Dict[str, Any]] = []
        for rf in route_features:
            coords = self._decode_osrm_steps(rf["steps_list"])
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "route_id": route_id,
                        "layer": rf["layer"],
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords,
                    },
                }
            )
        fc = {"type": "FeatureCollection", "features": features}
        filepath = os.path.join(self.save_dir, f"{route_id}_route.geojson")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)
        return filepath

    # ------------------------------------------------------------------
    # INDEX JSON
    # ------------------------------------------------------------------
    def build_index_json(
        self,
        route_id: str,
        solutions: List[Dict[str, Any]],
        geojson_route_name: str,
        geojson_markers_name: str,
    ) -> str:
        """
        Builds <route_id>.json with a fully JSON-safe structure:
          - route_id
          - solutions (cleaned)
          - geojson_route
          - geojson_markers
        """
        raw_index_data = {
            "route_id": route_id,
            "solutions": solutions,
            "geojson_route": geojson_route_name,
            "geojson_markers": geojson_markers_name,
        }
        index_data = self._json_safe(raw_index_data)
        filepath = os.path.join(self.save_dir, f"{route_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)
        return filepath