import os
from typing import Dict, List, Any, Literal
import numpy as np

from libraries.classes.osrm_api import OSRMClient
from libraries.classes.geojson_builder import GeoJSONBuilder
from libraries.config import PROBLEM_TYPES
from libraries.utils.algorithm.single_route.structured_route_builder import build_structured_route_data

def _get_E_value(E: float | List[float], i: int) -> float:
    if isinstance(E, (int, float)):
        return float(E)
    if isinstance(E, list):
        return float(E[i])
    if isinstance(E, np.ndarray):
        if E.ndim == 1:
            return float(E[i])
        return float(E.flatten()[i])
    return float(E)

def _compute_marker_meta(
    route_id: str,
    locations: List[Dict[str, Any]],
    E: float | List[float]
    ) -> Dict[int, Dict[str, Any]]:
    """
    Compute per-marker metadata used for marker popups.
    Indexed by route_number.
    """
    meta: Dict[int, Dict[str, Any]] = {}
    for loc in locations:
        i = int(loc["route_nr"])
        p = int(loc.get("n_postboxes", 1))
        Ei = _get_E_value(E, i)
        revenue = Ei * p
        meta[i] = {
            "route_id": str(route_id),
            "postboxes": p,
            "revenue": round(float(revenue), 2),
            "address": loc.get("address"),
        }
    return meta

def _compute_route_stops(
    route_id: str,
    R: List[int],
    significant: set[int],
    route_data: Dict[str, Any],
    E: float | List[float],
    APR: float,
    problem_type: PROBLEM_TYPES = "TSP",
) -> List[Dict[str, Any]]:
    """
    Compute per-stop table rows for a given route order R.
    Adds both:
      - sequence_index (position in route)
      - route_number (original node index)
    """
    if problem_type in {"OUT:TSP", "OUT:HPP"}:
        if route_data.get("nodes") is None:
            raise ValueError("Structured problem_type requires 'nodes' in route_data.")
        _, _, D_used = build_structured_route_data(
            D_big=route_data.get("Distance_Matrix"),
            nodes=route_data.get("nodes"),
        )
    else:
        D_used = route_data.get("Distance_Matrix")
    locations = route_data["data"].to_dict("records")
    stops: List[Dict[str, Any]] = []
    if not R:
        return stops
    n = len(R)
    for seq_idx, node_idx in enumerate(R):
        if problem_type in {"HPP","OUT:HPP"} and seq_idx == n - 1:
            next_node = None
            dist = None
        else:
            next_node = R[(seq_idx + 1) % n]
            dist = float(D_used[node_idx, next_node]) if D_used is not None else None
        loc = locations[node_idx]
        p = int(loc.get("n_postboxes", 1))
        Ei = _get_E_value(E, node_idx)
        revenue = Ei * p
        stops.append({
            "route_id": str(route_id),
            "sequence_index": seq_idx,      
            "route_number": int(node_idx),   
            "address": loc.get("address"),
            "postboxes": p,
            "revenue": round(float(revenue), 2),
            "distance_to_next": round(dist, 1) if dist is not None else None,
            "apr_cost": round(APR * dist, 2) if dist is not None else None,
            "is_significant_outlier": bool(node_idx in significant),
        })
    return stops

def build_route_geojson_bundle(
    route_id: str,
    route_data: Dict[str, Any],
    results_list: List[Dict[str, Any]],
    save_path: str,
    E: Any = 5.0,
    problem_type: PROBLEM_TYPES = "TSP",
    structure: str = "v1"
    ) -> Dict[str, Any]:
    """
    Builds 3 files for a single route in:
        <save_path>/routes/<route_id>/

      - <route_id>_markers.geojson
      - <route_id>_route.geojson
      - <route_id>.json   (metadata, including per-solution stops)

    Returns absolute paths for later indexing.
    """
    # -------------------------------------------------
    # Setup
    # -------------------------------------------------
    if structure == "v1":
        route_folder = os.path.join(save_path, "routes", str(route_id))
    elif structure == "v2":
        route_folder = save_path
    else:
        raise ValueError(f"Unknown structure mode: {structure}")
    os.makedirs(route_folder, exist_ok=True)
    geo = GeoJSONBuilder(route_folder)
    client = OSRMClient()
    locations = route_data["data"].to_dict("records")
    # -------------------------------------------------
    # Marker metadata (shared across solutions)
    # -------------------------------------------------
    marker_meta = _compute_marker_meta(
        route_id=str(route_id),
        locations=locations,
        E=E
    )
    # -------------------------------------------------
    # Classify markers per T1 / T2
    # -------------------------------------------------
    t1_normal, t1_out, t1_sig = [], [], []
    t2_normal, t2_out, t2_sig = [], [], []
    for r in results_list:
        significant = list(r["S_outlier"])
        all_out = set().union(*r["coverage_change"].keys()) if r["coverage_change"] else set()
        normal = [i for i in r["R_original"] if i not in all_out]
        nonsig = [i for i in all_out if i not in significant]
        if r["strict_order"]:
            t1_normal, t1_out, t1_sig = normal, nonsig, significant
        else:
            t2_normal, t2_out, t2_sig = normal, nonsig, significant
    # -------------------------------------------------
    # Compute per-solution stops
    # -------------------------------------------------
    for sol in results_list:
        sol_apr = float(sol.get("APR", 0.0))
        sol["stops_original"] = _compute_route_stops(
            route_id=str(route_id),
            R=sol["R_original"],
            significant=set(sol["S_outlier"]),
            route_data=route_data,
            E=E,
            APR=sol_apr,
            problem_type=problem_type,
        )
        sol["stops_optimal"] = _compute_route_stops(
            route_id=str(route_id),
            R=sol["R_star"],
            significant=set(sol["S_outlier"]),
            route_data=route_data,
            E=E,
            APR=sol_apr,
            problem_type=problem_type,
        )
    # -------------------------------------------------
    # Build marker GeoJSON (with metadata)
    # -------------------------------------------------
    markers_path = geo.build_markers_geojson(
        route_id=str(route_id),
        locations=locations,
        t1_normal=t1_normal,
        t1_outlier=t1_out,
        t1_sig=t1_sig,
        t2_normal=t2_normal,
        t2_outlier=t2_out,
        t2_sig=t2_sig,
        marker_meta=marker_meta,
    )
    # -------------------------------------------------
    # Build route LineStrings
    # -------------------------------------------------
    route_features = []
    for r in results_list:
        prefix = "T1" if r["strict_order"] else "T2"

        steps_orig = client.route_hamilton_path(locations, 
                                                R=r["R_original"],
                                                profile=r['profile']['profile'],
                                                problem_type=r["problem_type"])
        steps_opt = client.route_hamilton_path(locations, 
                                               R=r["R_star"],
                                               profile=r['profile']['profile'],
                                               problem_type=r["problem_type"])

        route_features.append({
            "layer": f"{prefix} Original",
            "steps_list": steps_orig,
        })
        route_features.append({
            "layer": f"{prefix} Optimal",
            "steps_list": steps_opt,
        })
    routes_path = geo.build_route_geojson(
        route_id=str(route_id),
        route_features=route_features,
    )
    # -------------------------------------------------
    # Build per-route index JSON
    # -------------------------------------------------
    index_path = geo.build_index_json(
        route_id=str(route_id),
        solutions=results_list,
        geojson_route_name=os.path.basename(routes_path),
        geojson_markers_name=os.path.basename(markers_path),
    )
    return {
        "route_id": str(route_id),
        "index": index_path,
        "markers": markers_path,
        "routes": routes_path,
    }