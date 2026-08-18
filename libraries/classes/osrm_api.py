import os
import requests
import math
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Optional, Literal
from libraries.config import PROBLEM_TYPES_SET

class OSRMClient:
    LOCAL_PROFILE_PORTS = {
        "foot": "http://localhost:5000",
        "car": "http://localhost:5001",
        "car-newyork": "http://localhost:5003",
        "bike": "http://localhost:5002",
        "bicycle": "http://localhost:5002",
    }
    PROFILE_ENV_VARS = {
        "foot": "OSRM_FOOT_URL",
        "car": "OSRM_CAR_URL",
        "car-newyork": "OSRM_CAR_NEWYORK_URL",
        "bicycle": "OSRM_BICYCLE_URL",
    }
    PROFILE_ALIASES = {
        "bike": "bicycle",
    }
    PROFILE_PATH_ALIASES = {
        "car-newyork": "car",
    }
    def __init__(
        self,
        base_url: str = "local",
        profile: str = "foot",
    ):
        profile = profile.lower()
        profile = self.PROFILE_ALIASES.get(profile, profile)
        self.profile = profile
        self._local_mode = base_url == "local"
        if base_url == "local":
            self.base_url = self._resolve_base_url(profile)
        else:
            # Remote / external OSRM → do not interfere
            self.base_url = base_url.rstrip("/")
    
    def _resolve_profile(self, profile: Optional[str]) -> str:
        if profile is None:
            return self.profile
        profile = profile.lower()
        return self.PROFILE_ALIASES.get(profile, profile)

    def _resolve_path_profile(self, profile: Optional[str]) -> str:
        resolved = self._resolve_profile(profile)
        return self.PROFILE_PATH_ALIASES.get(resolved, resolved)

    def _resolve_base_url(self, profile: Optional[str]) -> str:
        if not self._local_mode:
            return self.base_url

        resolved = self._resolve_profile(profile)
        if resolved not in self.LOCAL_PROFILE_PORTS:
            raise ValueError(
                f"Unsupported local profile '{resolved}'. "
                f"Supported: {list(self.LOCAL_PROFILE_PORTS)}"
            )

        env_var = self.PROFILE_ENV_VARS.get(resolved)
        return os.getenv(
            env_var,
            self.LOCAL_PROFILE_PORTS[resolved],
        ).rstrip("/")

    @staticmethod
    def _format_coordinates(locations: List[Dict[str, float]]):
        """
        Converts list of dicts with lon/lat into OSRM coordinate string.
        Input:[{'lon': 14.7, 'lat': 55.1}, ...]
        Returns: "lon1,lat1;lon2,lat2;lon3,lat3"
        """
        parts = []
        for loc in locations:
            lon = float(loc["lon"])
            lat = float(loc["lat"])
            parts.append(f"{lon},{lat}")
        return ";".join(parts)
    
    def table(
            self,
            locations: List[Dict[str, float]],
            annotations: Literal["distance", "duration"] = "distance",
            sources: Optional[List[int]] = None,
            destinations: Optional[List[int]] = None,
            fallback_coordinate: Literal["input", "snapped"] = "input",
            profile: Optional[str] = None,
            clip_negative: bool = True,
        ) -> Dict:
        """
        Calls OSRM /table/v1/<profile>/
        Docs: https://project-osrm.org/docs/v5.24.0/api/#table-service
        """
        base_url = self._resolve_base_url(profile)
        profile = self._resolve_path_profile(profile)
        coord_string = self._format_coordinates(locations)
        url = f"{base_url}/table/v1/{profile}/{coord_string}"
        params = {
            "annotations": annotations,
            "fallback_coordinate": fallback_coordinate,
        }
        if sources is not None:
            params["sources"] = ";".join(map(str, sources))
        if destinations is not None:
            params["destinations"] = ";".join(map(str, destinations))
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if clip_negative:
            key = "distances" if annotations == "distance" else "durations"
            matrix = data.get(key)
            if matrix is not None:
                for i, row in enumerate(matrix):
                    for j, val in enumerate(row):
                        if val is not None and val < 0:
                            matrix[i][j] = 0.0
        return data

    def table_chunked(
        self,
        locations: List[Dict[str, float]],
        chunk_size: int = 75,
        profile: Optional[str] = None,
        annotations: Literal["distance", "duration"] = "distance",
        clip_negative: bool = True,
        ) -> np.ndarray:
        n = len(locations)
        chunks = math.ceil(n / chunk_size)
        M = np.zeros((n, n))
        ranges = []
        for c in range(chunks):
            start = c * chunk_size
            end = min((c + 1) * chunk_size, n)
            ranges.append((start, end))
        key = "distances" if annotations == "distance" else "durations"
        for _, (s_i, e_i) in tqdm(
            enumerate(ranges),
            desc="OSRM Table Chunks",
            total=len(ranges),
            leave=False,
        ):
            loc_i = locations[s_i:e_i]
            for _, (s_j, e_j) in tqdm(
                enumerate(ranges),
                desc="  Inner chunks",
                total=len(ranges),
                leave=False,
            ):
                loc_j = locations[s_j:e_j]
                coords = loc_i + loc_j
                n_i = len(loc_i)
                n_j = len(loc_j)
                sources = list(range(n_i))
                destinations = list(range(n_i, n_i + n_j))
                result = self.table(
                    coords,
                    profile=profile,
                    annotations=annotations,
                    sources=sources,
                    destinations=destinations,
                    clip_negative=clip_negative,
                )
                block = np.array(result[key])
                M[s_i:e_i, s_j:e_j] = block
        return M

    def route(
            self,
            locations: List[Dict[str, float]],
            overview: Literal["false", "simplified", "full"] = "simplified",
            steps: bool = False,
            annotations: Optional[Literal["distance", "duration", "nodes", "weight", "datasources"]] = None,
            geometries: Literal["polyline", "polyline6", "geojson"] = "polyline",
            alternatives: bool = False,
            continue_straight: Optional[bool] = None,
            profile: Optional[str] = None,
        ):
        """
        Calls OSRM /route/v1/<profile>/
        Docs: https://project-osrm.org/docs/v5.24.0/api/#route-service
        """
        base_url = self._resolve_base_url(profile)
        profile = self._resolve_path_profile(profile)
        coord_string = self._format_coordinates(locations)
        url = f"{base_url}/route/v1/{profile}/{coord_string}"
        params = {
            "overview": overview,
            "steps": "true" if steps else "false",
            "alternatives": "true" if alternatives else "false",
            "geometries": geometries,
            "annotations": annotations if annotations else "false",
            "continue_straight": "true" if continue_straight else "false"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _dedupe_consecutive_locations(self, locs: list[dict]) -> list[dict]:
        if not locs:
            return []
        out = [locs[0]]
        for p in locs[1:]:
            if p["lon"] != out[-1]["lon"] or p["lat"] != out[-1]["lat"]:
                out.append(p)
        return out

    def _build_locations_for_route(
        self,
        *,
        locations: list[dict],
        R: list[int],
        problem_type: str,
    ) -> list[dict]:
        """
        Build OSRM-ready locations for a SINGLE route.

        locations:
            Address-level rows (each dict contains:
            lon, lat, unit_number,
            unit_start_point_lon/lat,
            unit_end_point_lon/lat)

        R:
            Sequence of route_nr values (visit order).

        problem_type:
            "TSP", "HPP", "OUT:TSP", "OUT:HPP"
        """
        if problem_type not in PROBLEM_TYPES_SET:
            raise ValueError(f"Unknown problem_type: {problem_type}")
        if not R:
            R = list(range(len(locations)))
        if len(R) > len(locations):
            raise ValueError(
                f"Length of R ({len(R)}) does not match number of locations ({len(locations)})."
            )
        # --------------------------------------------------
        # REQUIRED KEYS CHECK (problem-type aware)
        # --------------------------------------------------
        BASE_KEYS = {"lon", "lat"}
        STRUCTURED_KEYS = BASE_KEYS | {
            "unit_number",
            "unit_start_point_lon",
            "unit_start_point_lat",
            "unit_end_point_lon",
            "unit_end_point_lat",
        }
        if problem_type in {"TSP", "HPP"}:
            required_keys = BASE_KEYS
        elif problem_type in {"OUT:TSP", "OUT:HPP"}:
            required_keys = STRUCTURED_KEYS
        else:
            raise ValueError(f"Unknown problem_type: {problem_type}")
        for i, row in enumerate(locations):
            missing = required_keys - row.keys()
            if missing:
                raise KeyError(
                    f"Location row {i} is missing required keys: {sorted(missing)}"
                )
        # --------------------------------------------------
        # Build lookup: route_nr -> row
        # --------------------------------------------------
        def addr(rn: int) -> dict:
            row = locations[rn]
            return {"lon": float(row["lon"]), 
                    "lat": float(row["lat"])}

        def unit_start(rn: int) -> dict:
            row = locations[rn]
            return {
                "lon": float(row["unit_start_point_lon"]),
                "lat": float(row["unit_start_point_lat"]),
            }

        def unit_end(rn: int) -> dict:
            row = locations[rn]
            return {
                "lon": float(row["unit_end_point_lon"]),
                "lat": float(row["unit_end_point_lat"]),
            }

        def unit_of(rn: int) -> int:
            return int(locations[rn]["unit_number"])

        # ==================================================
        # UNSTRUCTURED (TSP / HPP)
        # ==================================================
        if problem_type in {"TSP", "HPP"}:
            path = [addr(rn) for rn in R]
            if problem_type == "TSP":
                path.append(addr(R[0]))  
            return self._dedupe_consecutive_locations(path)

        # ==================================================
        # STRUCTURED (OUT:TSP / OUT:HPP)
        # ==================================================
        
        path: list[dict] = [addr(R[0])]
        for i in range(len(R) - 1):
            cur = R[i]
            nxt = R[i + 1]

            if unit_of(cur) != unit_of(nxt):
                path.append(unit_end(cur))
                path.append(unit_start(nxt))
            path.append(addr(nxt))

        # ----------------------------------
        # Closing logic
        # ----------------------------------
        if problem_type == "OUT:TSP":
            last = R[-1]
            first = R[0]
            if unit_of(last) != unit_of(first):
                path.append(unit_end(last))
                path.append(unit_start(first))
            path.append(addr(first))
        return self._dedupe_consecutive_locations(path)

    def route_hamilton_path(
        self,
        locations: List[Dict],
        R: Optional[List[int]] = None,
        profile: Optional[str] = None,
        problem_type: Literal["TSP", "HPP", "OUT:TSP", "OUT:HPP"] = "TSP",
    ):
        """
        Compute a Hamiltonian route using OSRM routing.

        For:
        - TSP / HPP       → address-only routing
        - OUT:TSP / OUT:HPP → unit-aware routing using start/end points

        Parameters
        ----------
        locations : List[Dict]
            Address-level rows for ONE route. Each row must contain:
            lon, lat (and unit_* fields for structured problems).

        R : Optional[List[int]]
            Route order as indices into `locations`.

        profile : Optional[str]
            OSRM routing profile ("foot", "car", …).

        problem_type : str
            One of {"TSP", "HPP", "OUT:TSP", "OUT:HPP"}.

        Returns
        -------
        List[List[Dict]]
            OSRM step lists, one per routed leg.
        """
        # --------------------------------------------
        # Resolve profile
        # --------------------------------------------
        if profile is None:
            profile = self.profile
        else:
            profile = self._resolve_profile(profile)

        n = len(locations)
        if n < 2:
            return []

        # --------------------------------------------
        # Default route order
        # --------------------------------------------
        if R is None:
            R = list(range(n))
        for idx in R:
            if not isinstance(idx, int):
                raise TypeError(f"Route index {idx!r} is not an integer.")
            if idx < 0 or idx >= n:
                raise ValueError(
                    f"Route index {idx} out of bounds. Must be between 0 and {n-1}."
                )
        if len(R) < 2:
            return []
        # --------------------------------------------
        # Build expanded routing locations
        # --------------------------------------------
        path_locations = self._build_locations_for_route(
            locations=locations,
            R=R,
            problem_type=problem_type,
        )

        if len(path_locations) < 2:
            return []

        # --------------------------------------------
        # Fetch OSRM legs sequentially
        # --------------------------------------------
        all_steps = []
        for i in tqdm(
            range(len(path_locations) - 1),
            desc="Routing Hamiltonian path",
            leave=False,
        ):
            a = path_locations[i]
            b = path_locations[i + 1]
            result = self.route(
                [a, b],
                profile=profile,
                steps=True,
                overview="simplified",
            )
            try:
                steps = result["routes"][0]["legs"][0]["steps"]
            except (KeyError, IndexError):
                raise RuntimeError(
                    f"OSRM did not return valid steps for leg {i} -> {i + 1}."
                )
            all_steps.append(steps)
        return all_steps


