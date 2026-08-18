from pathlib import Path
from typing import Dict, Any, List

import folium
from libraries.classes.osm_segment_api import OSMSegmentClient


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _ensure_output_dir() -> Path:
    out = Path(__file__).parent / "maps" / "grouped" 
    out.mkdir(parents=True, exist_ok=True)
    return out


def _side_color(side: str | None) -> str:
    if side == "left":
        return "blue"
    if side == "right":
        return "red"
    if side == "center":
        return "purple"
    return "gray"


# --------------------------------------------------
# Public plotting function
# --------------------------------------------------
def plot_snap_with_unit(
    *,
    snap: Dict[str, Any],
    group: Dict[str, Any],
    index: int,
) -> Path:
    """
    Plot:
    - input point
    - snapped/projected point
    - unit start + end points
    - side of road
    """

    # --------------------------------------------------
    # Map center = snapped point
    # --------------------------------------------------
    center_lat = snap["projected_point"]["y"]
    center_lon = snap["projected_point"]["x"]

    side = snap["geometry"].get("side_of_road")
    color = _side_color(side)

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # --------------------------------------------------
    # Input point
    # --------------------------------------------------
    folium.CircleMarker(
        location=[snap["input"]["y"], snap["input"]["x"]],
        radius=4,
        color="black",
        fill=True,
        popup="Input point",
    ).add_to(m)

    # --------------------------------------------------
    # Snapped / projected point
    # --------------------------------------------------
    folium.CircleMarker(
        location=[center_lat, center_lon],
        radius=6,
        color=color,
        fill=True,
        popup=f"Snapped point (side={side})",
    ).add_to(m)

    # --------------------------------------------------
    # Unit start / end
    # --------------------------------------------------
    folium.Marker(
        location=[
            group["start_point"]["lat"],
            group["start_point"]["lon"],
        ],
        icon=folium.Icon(color="green", icon="play"),
        popup="Unit start",
    ).add_to(m)

    folium.Marker(
        location=[
            group["end_point"]["lat"],
            group["end_point"]["lon"],
        ],
        icon=folium.Icon(color="purple", icon="stop"),
        popup="Unit end",
    ).add_to(m)

    # --------------------------------------------------
    # Save
    # --------------------------------------------------
    out_dir = _ensure_output_dir()
    filename = f"snap_unit_{index:03d}_seg_{snap['segment']['segment_id']}.html"
    out_path = out_dir / filename
    m.save(out_path)

    return out_path


# --------------------------------------------------
# Manual execution (mirrors test)
# --------------------------------------------------
if __name__ == "__main__":
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:4326",
        output_crs="EPSG:4326",
        allowed_highways={
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "living_street",
        },
    )

    POINTS: List[Dict[str, float]] = [
        {"lon": 14.710637, "lat": 55.121750},
        {"lon": 14.710870, "lat": 55.122063},
        # {"lon": 14.7112, "lat": 55.1221},
        # {"lon": 14.7107, "lat": 55.1215},
        # {"lon": 14.7108, "lat": 55.1216},
        # {"lon": 14.7108, "lat": 55.1218},
    ]

    snaps = client.snap_nearest_batch(
            POINTS,
            x_key="lon",
            y_key="lat",
            show_progress=True,
        )
    from pprint import pprint
    
    for i, snap in enumerate(snaps):
        group = client.group_segments_on_side(
            snap,
            allowed_highways=client.allowed_highways,
            use_rotated_side=True,
            entry_angle_deg=-60.0,
            exit_angle_deg=60.0,
            offset_m=2.5,
        )
        pprint(group)
        path = plot_snap_with_unit(
            snap=snap,
            group=group,
            index=i,
        )
        print(f"Wrote map: {path}")
