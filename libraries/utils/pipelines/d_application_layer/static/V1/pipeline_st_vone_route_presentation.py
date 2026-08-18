from typing import Any, Dict, List, Tuple, Optional

from libraries.utils.visualization.map_pipeline import build_route_map
from libraries.utils.visualization.html_generator import render_route_page
from libraries.utils.visualization.visualisation_helpers import generate_result_dict


def present_single_route_static(
    *,
    route_id: Any,
    data: Dict[str, Any],
    results_route_list: List[Dict[str, Any]],
    views_root: str,
    all_maps: List[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
    kpi_mapping: List[Dict[str, Any]],
    route_type: str,
    html_render: bool,
    template_root: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Render static presentation for a single route:
    - route map
    - route HTML page
    - aggregate results for index page
    """

    if not html_render:
        return all_maps, all_results, []

    # ----------------------------------------
    # Map rendering
    # ----------------------------------------
    map_info = build_route_map(
        route_id=str(route_id),
        route_data=data,
        results_list=results_route_list,
        saved_or_show="save",
        views_root=views_root,
    )

    # ----------------------------------------
    # Route page rendering
    # ----------------------------------------
    render_route_page(
        route_id=str(route_id),
        map_file=map_info["map_file"],
        results=results_route_list,
        saved_or_show="save",
        views_root=views_root,
        template_root=template_root
    )
    all_maps.append(map_info)

    # ----------------------------------------
    # Results aggregation for index
    # ----------------------------------------
    all_results, kpis = generate_result_dict(
        route_id=str(route_id),
        all_results=all_results,
        results_route_list=results_route_list,
        kpi_mapping=kpi_mapping,
        route_type=route_type,
    )
    return all_maps, all_results, kpis
