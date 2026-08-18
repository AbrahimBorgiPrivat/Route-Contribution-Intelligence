import os
from pathlib import Path
from typing import Optional
import tempfile
import webbrowser
from jinja2 import Environment, FileSystemLoader

def render_route_page(
    route_id: str,
    map_file: str,
    results: list,
    saved_or_show: str = "save",    
    views_root: str = "./views/v1/static/",
    template_root: Optional[str] = None,
    ):
    """
    Render a route-specific detail page:
        route_<route_id>.html

    map_file : path to already saved folium map HTML
    results : list of dicts from generate_route_maps
    """
    map_file = '..\\' + map_file
    views_root = Path(views_root)
 
    if template_root is None:
        template_dir = views_root / "templates"
    else:
        template_dir = Path(template_root)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("route_page.html")
    html = template.render(
        route_id=route_id,
        map_file=map_file,
        results=results,
    )
    # -------------------------------
    # SHOW MODE (temporary HTML)
    # -------------------------------
    if saved_or_show.lower() == "show":
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + os.path.abspath(temp_path))
        print(f"[INFO] Showing route page in browser: {temp_path}")
        return {"html_path": temp_path}
    # -------------------------------
    # SAVED MODE
    # -------------------------------
    output_dir = views_root / "routes"
    os.makedirs(output_dir, exist_ok=True)
    abs_output_path = os.path.abspath(os.path.join(output_dir, f"route_{route_id}.html"))
    with open(abs_output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Route page saved: {abs_output_path}")
    rel_output_path = f"{output_dir}/route_{route_id}.html"
    print(rel_output_path)
    return {"html_path": rel_output_path}

def render_index_page(
    routes: list,
    kpis: list,               
    saved_or_show="save",
    views_root: str = "./views/v1/static/",
    template_root: Optional[str] = None,
    ):
    views_root = Path(views_root)
    if template_root is None:
        template_dir = views_root / "templates"
    else:
        template_dir = Path(template_root)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index_page.html")
    html = template.render(
        routes=routes,
        kpis=kpis,             
        map_file="./maps/all_routes_map.html"
    )
    if saved_or_show == "show":
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + os.path.abspath(temp_path))
        return {"html_path": temp_path}
    output_path = views_root / "index.html"
    #output_path = output_path.replace("\\", "/")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Index page saved → {output_path}")
    return {"html_path": output_path}
