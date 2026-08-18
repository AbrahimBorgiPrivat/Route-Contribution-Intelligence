from typing import List, Dict, Any, Literal, Optional
from pathlib import Path
import os
import json

def generate_result_dict(
    route_id: str,
    all_results: list,
    results_route_list: List[Dict],
    kpi_mapping: List[Dict],
    route_type: Literal["type1", "type2", "both"] = "both"
    ):
    """
    Generalizes KPI + output dict creation based on a flat KPI mapping list.
    """
    # ---------------------------------------------------------
    # VALIDATE MAPPING FORMA
    # ---------------------------------------------------------
    REQUIRED_FIELDS = {"name", "key", "type", "val"}
    VALID_TYPES = {"type1", "type2", "both"}

    for _, entry in enumerate(kpi_mapping):
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            raise ValueError(
                f"KPI mapping entry {entry} is missing required fields: {missing}"
            )
        if entry["type"] not in VALID_TYPES:
            raise ValueError(
                f"KPI mapping entry {entry} has invalid type '{entry['type']}'. "
                f"Must be one of {VALID_TYPES}."
            )
        if not callable(entry["val"]):
            raise ValueError(
                f"KPI mapping entry {entry} has a non-callable 'val'. "
                f"It must be a lambda/function."
            )
        
    # ---------------------------------------------------------
    # Identify rows (type1 / type2)
    # ---------------------------------------------------------
    t1_row = next((r for r in results_route_list if r["strict_order"] is True), None)
    t2_row = next((r for r in results_route_list if r["strict_order"] is False), None)
    row_lookup = {
        "type1": t1_row,
        "type2": t2_row,
        "both":  t1_row or t2_row 
    }
    # -------------------------
    # Build result entry
    # -------------------------
    result_entry = {"route_id": route_id}
    for entry in kpi_mapping:
        kpi_type = entry["type"]
        if route_type not in ("both", kpi_type):
            continue
        row = row_lookup.get(kpi_type)
        if row is None:
            result_entry[entry["key"]] = None
        else:
            try:
                result_entry[entry["key"]] = entry["val"](row)
            except Exception:
                result_entry[entry["key"]] = None
    all_results.append(result_entry)
    # -------------------------
    # Build KPI list for index
    # -------------------------
    kpis = [
        {"name": entry["name"], "key": entry["key"]}
        for entry in kpi_mapping
        if route_type in ("both", entry["type"])
    ]
    return all_results, kpis

def build_routes_index_json(
    base_dir: str,
    kpi_mapping: List[Dict[str, Any]],
    *,
    use_data: bool = True,
    route_outputs: Optional[List[Dict[str, Any]]] = None,
    filename: str = "routes_index.json",
    ) -> str:
    """
    Build routes_index.json in <base_dir>.
    Two modes are supported:
    1) use_data = True
       Uses route_outputs (typically produced by a pipeline run).
       Expects each entry to contain:
         {
           "route_id": <id>,
           "index": <absolute path to <route_id>.json>
         }
    2) use_data = False
       Scans the filesystem:
         <base_dir>/routes/<route_id>/<route_id>.json
       and includes all valid route JSON files found.

    The KPI mapping is passed through unchanged.
    """
    routes_entries: List[Dict[str, str]] = []
    # ---------------------------------------------------------
    # MODE 1: Use provided route outputs (pipeline-driven)
    # ---------------------------------------------------------
    if use_data:
        if not route_outputs:
            raise ValueError(
                "use_data=True requires route_outputs to be provided."
            )
        for entry in route_outputs:
            if "route_id" not in entry or "index" not in entry:
                continue
            route_id = entry["route_id"]
            route_json_abs = entry["index"]
            if not os.path.isfile(route_json_abs):
                continue
            relative_path = os.path.relpath(route_json_abs, base_dir).replace(os.sep, "/")
            routes_entries.append(
                {
                    "route_id": str(route_id),
                    "path": relative_path,
                }
            )
    # ---------------------------------------------------------
    # MODE 2: Scan filesystem (state-driven)
    # ---------------------------------------------------------
    else:
        routes_dir = os.path.join(base_dir, "routes")
        if not os.path.isdir(routes_dir):
            raise FileNotFoundError(
                f"Routes directory not found: {routes_dir}"
            )
        for route_id in sorted(os.listdir(routes_dir)):
            route_folder = os.path.join(routes_dir, route_id)
            if not os.path.isdir(route_folder):
                continue
            route_json = os.path.join(route_folder, f"{route_id}.json")
            if not os.path.isfile(route_json):
                continue
            try:
                with open(route_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            if "route_id" not in data:
                continue
            relative_path = os.path.relpath(route_json, base_dir).replace(os.sep, "/")
            routes_entries.append(
                {
                    "route_id": str(data["route_id"]),
                    "path": relative_path,
                }
            )
    # ---------------------------------------------------------
    # Write index file
    # ---------------------------------------------------------
    index_data = {
        "routes": routes_entries,
        "kpis": kpi_mapping,
    }
    index_path = os.path.join(base_dir, filename)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)
    return index_path

def build_v2_registry_json(
    *,
    base_dir: str,
    filename: str = "registry.json",
    ) -> str:
    """
    Build flat registry.json for Application v2.
    """
    base_path = Path(base_dir)
    registry: List[Dict[str, Any]] = []
    if not base_path.exists():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")
    for label_dir in base_path.iterdir():
        if not label_dir.is_dir():
            continue
        label = label_dir.name
        for route_dir in label_dir.iterdir():
            if not route_dir.is_dir():
                continue
            route_id = route_dir.name
            for apr_dir in route_dir.iterdir():
                if not apr_dir.is_dir():
                    continue
                apr_profile = apr_dir.name
                for week_dir in apr_dir.iterdir():
                    if not week_dir.is_dir():
                        continue
                    week_profile = week_dir.name
                    route_json = week_dir / f"{route_id}.json"
                    markers_geo = week_dir / f"{route_id}_markers.geojson"
                    route_geo = week_dir / f"{route_id}_route.geojson"
                    if not route_json.exists():
                        continue
                    entry = {
                        "label": label,
                        "route_id": str(route_id),
                        "APR_profile": apr_profile,
                        "Week_Profile": week_profile,
                        "route_json": route_json.relative_to(base_path).as_posix(),
                        "markers_geojson": markers_geo.relative_to(base_path).as_posix() if markers_geo.exists() else None,
                        "route_geojson": route_geo.relative_to(base_path).as_posix() if route_geo.exists() else None,
                    }
                    registry.append(entry)
    registry_path = base_path / filename
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    return str(registry_path)


def build_v2_scenario_metadata_json(
    *,
    base_dir: str,
    filename: str = "scenario_metadata.json",
    label_explanations: Optional[Dict[str, str]] = None,
    apr_explanations: Optional[Dict[str, str]] = None,
    revenue_explanations: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build shared scenario metadata JSON for Application v2.
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")

    metadata = {
        "labels": label_explanations or {},
        "APR_profiles": apr_explanations or {},
        "week_profiles": revenue_explanations or {},
    }

    metadata_path = base_path / filename
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    return str(metadata_path)
