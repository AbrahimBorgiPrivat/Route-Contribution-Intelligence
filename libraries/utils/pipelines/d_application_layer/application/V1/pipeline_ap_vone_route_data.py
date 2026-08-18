from typing import Dict, Any, List
import numpy as np
from libraries.utils.visualization.geojson_pipeline import build_route_geojson_bundle

def build_single_route_data(
    *,
    route_id: str,
    route_data: Dict[str, Any],
    results_route_list: List[Dict[str, Any]],
    save_dir: str,
    E: float | List[float] | np.ndarray = 5.0,
    problem_type: str,
    structure: str = "v1"
) -> Dict[str, Any]:
    """
    Build GeoJSON + metadata outputs for a single route.

    Returns a descriptor used later for index building.
    """
    # ----------------------------------------
    # Resolve E 
    # ----------------------------------------
    
    if "revenue" in route_data['data']:
        E_used = route_data['data']["revenue"].to_numpy(dtype=float)
    else:
        E_used = E
        
    files = build_route_geojson_bundle(
        route_id=route_id,
        route_data=route_data,
        results_list=results_route_list,
        save_path=save_dir,
        E=E_used,
        problem_type=problem_type,
        structure=structure
    )

    return files
