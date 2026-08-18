import os
from pathlib import Path
from typing import Dict, List, Any
from libraries.classes.osrm_api import OSRMClient
from libraries.classes.plot_route import RoutePlotterFolium

def build_route_map(route_id: str, 
                    route_data: Dict[str, Any],
                    results_list: List[Dict[str, Any]],
                    style: Dict[str, Any] = None,
                    views_root: str = "./views/v1/static/", 
                    saved_or_show: str = "save",
                    ) -> Dict[str, Any]:
    """
    Creates a folium map with all Type1 and Type2 layers.
    """
    default_style = { "t1_route_original": {"color": "black", "weight": 6},
                     "t1_route_star": {"color": "darkgreen", "weight": 5}, 
                     "t1_normal": {"color": "blue"}, 
                     "t1_outlier": {"color": "orange"}, 
                     "t1_sig_outlier": {"color": "red"}, 
                     "t2_route_original": {"color": "purple", "weight": 6}, 
                     "t2_route_star": {"color": "cyan", "weight": 5}, 
                     "t2_normal": {"color": "darkblue"}, 
                     "t2_outlier": {"color": "gold"}, 
                     "t2_sig_outlier": {"color": "darkred"}, 
                     } 
    if style: 
        default_style.update(style)
    locations = route_data['data'].to_dict("records")
    client = OSRMClient()
    plotter = RoutePlotterFolium()
    for r in results_list:
        strict = r["strict_order"]
        prefix = "t1" if strict else "t2"
        name_prefix = "Type1" if strict else "Type2"
        # --------------------------------------------
        # ROUTES 
        # --------------------------------------------
        steps_orig = client.route_hamilton_path(locations, 
                                                R=r["R_original"],
                                                profile=r['profile']['profile'],
                                                problem_type=r["problem_type"])
        plotter.add_route_from_steps(
            steps_orig,
            name=f"{name_prefix}: Route Original",
            color=default_style[f"{prefix}_route_original"]["color"],
            weight=default_style[f"{prefix}_route_original"]["weight"],
        )

        steps_star = client.route_hamilton_path(locations, 
                                                R=r["R_star"],
                                                profile=r['profile']['profile'],
                                                problem_type=r["problem_type"])
        plotter.add_route_from_steps(
            steps_star,
            name=f"{name_prefix}: Route After Outlier Removal",
            color=default_style[f"{prefix}_route_star"]["color"],
            weight=default_style[f"{prefix}_route_star"]["weight"],
        )
        # --------------------------------------------
        # POINTS 
        # --------------------------------------------
        significant = list(r["S_outlier"])
        all_out = set().union(*r["coverage_change"].keys()) if r["coverage_change"] else set()
        normal = [i for i in r["R_original"] if i not in all_out]
        nonsig = [i for i in all_out if i not in significant]
        if normal:
            plotter.add_points(
                [locations[i] for i in normal],
                name=f"{name_prefix}: Normal",
                labels=normal,
                color=default_style[f"{prefix}_normal"]["color"]
            )
        if nonsig:
            plotter.add_points(
                [locations[i] for i in nonsig],
                name=f"{name_prefix}: Outliers",
                labels=nonsig,
                color=default_style[f"{prefix}_outlier"]["color"]
            )
        if significant:
            plotter.add_points(
                [locations[i] for i in significant],
                name=f"{name_prefix}: Significant",
                labels=significant,
                color=default_style[f"{prefix}_sig_outlier"]["color"]
            )
    # --------------------------------------------
    # Finalize controls
    # --------------------------------------------
    plotter.add_layer_control()
    if saved_or_show == "show":
        plotter.show_map(map_file)
    else:
        views_root = Path(views_root)
        save_path = views_root / "maps"
        os.makedirs(save_path, exist_ok=True)
        abs_map_path = os.path.abspath(os.path.join(save_path, f"route_{route_id}_map.html"))
        plotter.save_map(abs_map_path)
        print(f"[OK] Saved map → {abs_map_path}")
        routes_dir = os.path.abspath(views_root)
        map_file = os.path.relpath(abs_map_path, routes_dir)
    return {
        "map_file": map_file,
        "plotter": plotter,
    }

def combine_all_route_maps(route_maps, 
                           views_root: str = "./views/v1/static/") -> str:
    """
    Combine multiple RoutePlotterFolium maps
    """
    if not route_maps:
        raise ValueError("No route maps to combine.")
    first_plotter = route_maps[0]["plotter"]
    base = RoutePlotterFolium(
        tiles=first_plotter.tiles,
        zoom_start=first_plotter.zoom_start
    )
    lat, lon = first_plotter.center
    base.init_map(lat, lon)
    # 1) Group FeatureGroups by their layer name
    grouped = {}
    for entry in route_maps:
        for fg in entry["plotter"].feature_groups:
            if hasattr(fg, "layer_name"):
                name = fg.layer_name
            elif hasattr(fg, "name"):
                name = fg.name
            elif hasattr(fg, "_name"):
                name = fg._name
            else:
                raise RuntimeError("FeatureGroup has no valid name attribute.")
            grouped.setdefault(name, []).append(fg)
    # 2) Merge via clone_child()
    for name, fg_list in grouped.items():
        unified = base.create_feature_group(name)
        for fg in fg_list:
            for child in fg._children.values():
                clone = base.clone_child(child)
                if clone:
                    unified.add_child(clone)
        base.add_feature_group(unified)
    # 3) Add layer control through class
    base.add_layer_control()
    # 4) Save through class
    views_root = Path(views_root)
    output_path = views_root / "maps/all_routes_map.html"
    base.save_map(output_path)
    return output_path