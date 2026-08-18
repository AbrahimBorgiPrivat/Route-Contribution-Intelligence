from typing import Dict, List, Any, Optional

from libraries.utils.visualization.map_pipeline import combine_all_route_maps
from libraries.utils.visualization.html_generator import render_index_page


def present_static_index(
    *,
    all_maps: List[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
    kpis: List[Dict[str, Any]],
    views_root: str,
    html_render: bool,
    template_root: Optional[str] = None,
) -> None:
    """
    Render global static presentation (v1):

    - Combine all per-route maps into one map
    - Render index HTML page

    Parameters
    ----------
    all_maps:
        List of map_info dicts returned by build_route_map.
    all_results:
        Aggregated per-route results used by the index page.
    kpis:
        KPI configuration used for table rendering.
    views_root:
        Root directory for static output (maps/, routes/, index.html).
    html_render:
        If False, function is a no-op.
    template_root:
        Optional override for template directory (used in tests).
        If None, defaults to views_root / "templates".
    """

    if not html_render or not all_maps:
        return

    combine_all_route_maps(
        route_maps=all_maps,
        views_root=views_root,
    )

    render_index_page(
        routes=all_results,
        kpis=kpis,
        saved_or_show="save",
        views_root=views_root,
        template_root=template_root
    )
