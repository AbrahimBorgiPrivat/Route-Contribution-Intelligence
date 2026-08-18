from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import folium
import pandas as pd

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
)


# --------------------------------------------------
# Constants (per your request)
# --------------------------------------------------
DATASET_PATH = "./libraries/simulations/_data/routes/tsp_simulationdata.csv"
OUTPUT_DIR = Path("libraries/simulations/_folium/maps/grouped")


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def _coerce_locations_df(route_prep_data: Dict[str, Any]) -> pd.DataFrame:
    if "data" not in route_prep_data:
        raise KeyError(
            "RoutePrep.data missing key 'data'. "
            "Expected a pandas DataFrame with unit geometry."
        )

    data = route_prep_data["data"]
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list):
        return pd.DataFrame(data)

    raise TypeError(
        f"Unsupported type for RoutePrep.data['data']: {type(data)}"
    )


def _mean_center(df: pd.DataFrame) -> Tuple[float, float]:
    return float(df["lat"].mean()), float(df["lon"].mean())


# --------------------------------------------------
# Public API
# --------------------------------------------------
def plot_first_route_units_grouped(
    *,
    file_path: str = DATASET_PATH,
    col_map: Dict[str, Dict[str, Any]],
    route_type: str = "both",
    APR: float | Dict[str, Any] = 0.03,
    start_routes: Optional[int] = None,
    max_routes: Optional[int] = 1,
    solver_tsp: str = "ortools",
    solver_hpp: str = "ortools",
    deterministic_tsp: bool = True,
    deterministic_hpp: bool = True,
    chunk_size_osm: int | None = 2,
    chunk_size_osrm: int = 50,
    use_rotated_side: bool = True,
    offset_m: float = 2.5,
    entry_angle_deg: float = -60.0,
    exit_angle_deg: float = 60.0,
    zoom_start: int = 16,
    tiles: str = "OpenStreetMap",
) -> Path:
    """
    Plot FIRST route in dataset:
      - base address (lon, lat)
      - unit start point
      - unit end point

    All plotted on ONE folium map.
    Each marker tooltip shows unit_number.
    """

    # --------------------------------------------------
    # Step 1: build pipeline context
    # --------------------------------------------------
    ctx = init_pipeline_context(
        file_path=file_path,
        col_map=col_map,
        route_type=route_type,
        A_kwargs=None,
        B_kwargs=None,
        U_kwargs=None,
        APR=APR,
        start_routes=start_routes,
        max_routes=max_routes,
    )

    if not ctx.route_ids:
        raise ValueError("No routes found in dataset.")

    route_id = ctx.route_ids[0]

    # --------------------------------------------------
    # Step 2: prepare route (unit geometry included)
    # --------------------------------------------------
    route_prep = prepare_route_and_matrices(
        route_id=route_id,
        df=ctx.df,
        APR=ctx.APR,
        solver_tsp=solver_tsp,
        solver_hpp=solver_hpp,
        deterministic_tsp=deterministic_tsp,
        deterministic_hpp=deterministic_hpp,
        allowed_highways=["primary",
                          "secondary",
                          "tertiary",
                          "residential",
                          "living_street",
                        ],
        chunk_size_osm=chunk_size_osm,
        chunk_size_osrm=chunk_size_osrm,
        use_rotated_side=use_rotated_side,
        offset_m=offset_m,
        entry_angle_deg=entry_angle_deg,
        exit_angle_deg=exit_angle_deg,
    )

    df_loc = _coerce_locations_df(route_prep.data)
    print(df_loc[df_loc["unit_number"].isin([5, 8])])
    required_cols = [
        "lon", "lat",
        "unit_number",
        "unit_start_point_lon", "unit_start_point_lat",
        "unit_end_point_lon", "unit_end_point_lat",
    ]
    missing = [c for c in required_cols if c not in df_loc.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    center_lat, center_lon = _mean_center(df_loc)

    # --------------------------------------------------
    # Step 3: build map
    # --------------------------------------------------
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=tiles,
        control_scale=True,
    )

    for _, row in df_loc.iterrows():
        uid = row["unit_number"]
        srow = row["side_of_road"]

        # Base address
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=4,
            color="black",
            fill=True,
            fill_opacity=0.9,
            tooltip=f"unit_id={uid} | side of road={srow}",
            popup=f"unit_id={uid} | base address",
        ).add_to(m)

        # Unit start
        folium.Marker(
            location=[row["unit_start_point_lat"], row["unit_start_point_lon"]],
            icon=folium.Icon(color="green", icon="play"),
            tooltip=f"unit_id={uid} | side of road={srow}",
            popup=f"unit_id={uid} | unit start",
        ).add_to(m)

        # Unit end
        folium.Marker(
            location=[row["unit_end_point_lat"], row["unit_end_point_lon"]],
            icon=folium.Icon(color="purple", icon="stop"),
            tooltip=f"unit_id={uid} | side of road={srow}",
            popup=f"unit_id={uid} | unit end",
        ).add_to(m)

    # --------------------------------------------------
    # Step 4: save map
    # --------------------------------------------------
    out_dir = _ensure_output_dir()
    out_path = out_dir / f"grouped_units_first_route_{route_id}.html"
    m.save(out_path)

    print(f"[OK] Grouped unit map written → {out_path}")
    return out_path


# --------------------------------------------------
# Manual run
# --------------------------------------------------
if __name__ == "__main__":
    COL_MAP = {"route_id": { "name": "id" },
            "lon":      { "name": "vejx" },
            "lat":      { "name": "vejy" },
            "line_nr":  { "name": "linienr" },
            "address": { 
                "fields": ["adresse"],
                "separator": "; "
            },
            "transform": {
                "convert_from": "EPSG:25832",
                "convert_to":   "EPSG:4326"
            },
            "type": {
                "name": "beregning",
                "foot":  {"val": 0, "annotations": "distance"},
                "car":   {"val": 1, "annotations": "duration"},
                "cycle": {"val": 2, "annotations": "distance"}
            },
            "problem_type": {
                "name": "beregning",
                "HPP": [1],
                "OUT:TSP": [0, 2]
            }
            }

    plot_first_route_units_grouped(
        col_map=COL_MAP,
        route_type="both",
        APR=0.03,
    )
