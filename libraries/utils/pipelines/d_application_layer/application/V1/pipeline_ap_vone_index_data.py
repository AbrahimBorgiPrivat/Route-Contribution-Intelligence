from typing import List, Dict, Any
from libraries.utils.visualization.visualisation_helpers import build_routes_index_json

def build_data_index(
    *,
    save_dir: str,
    kpi_mapping: List[Dict[str, Any]],
    route_outputs: List[Dict[str, Any]],
    use_data: bool,
    index_filename: str,
) -> str:
    """
    Build routes_index.json for data pipeline.
    """

    return build_routes_index_json(
        base_dir=save_dir,
        kpi_mapping=kpi_mapping,
        use_data=use_data,
        route_outputs=route_outputs,
        filename=index_filename,
    )
