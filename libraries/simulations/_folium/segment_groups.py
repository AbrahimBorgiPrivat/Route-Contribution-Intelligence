from pathlib import Path
from typing import Dict, Any

import folium
from libraries.classes.osm_segment_api import OSMSegmentClient
# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _ensure_output_dir() -> Path:
    out = Path(__file__).parent / "maps" / "grouped"
    out.mkdir(parents=True, exist_ok=True)
    return out
# --------------------------------------------------
# Public plotting function
# --------------------------------------------------

def plot_segment_group(
    *,
    seg: Dict[str, Any],
    group: Dict[str, Any],
    filename: str | None = None,
) -> Path:
    """
    Plot a snapped point together with its grouped road segments.

    Parameters
    ----------
    seg :
        Single element from snap_nearest_batch (segments[0])
    group :
        Output from OSMSegmentClient.group_segments_on_side
    filename :
        Optional filename (without path). Auto-generated if None.

    Returns
    -------
    Path to generated HTML file
    """

    # ----------------------------------------------
    # Map center (use projected point)
    # ----------------------------------------------
    center_lat = seg["projected_point"]["y"]
    center_lon = seg["projected_point"]["x"]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # ----------------------------------------------
    # Plot snapped input point
    # ----------------------------------------------
    folium.CircleMarker(
        location=[center_lat, center_lon],
        radius=6,
        color="red",
        fill=True,
        fill_opacity=0.9,
        popup="Snapped input point",
    ).add_to(m)

    # ----------------------------------------------
    # Plot grouped segment endpoints
    # ----------------------------------------------
    for sid, idx in group["segments"]:
        # We only have endpoints, not full geometry – plot endpoints
        if idx == 0:
            color = "blue"
        elif idx < 0:
            color = "green"
        else:
            color = "purple"

        folium.Marker(
            location=[
                center_lat,  # placeholder, overridden below
                center_lon,
            ],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size: 10pt;
                    color: {color};
                    font-weight: bold;
                ">
                    {idx}
                </div>
                """
            ),
            popup=f"segment_id={sid}, seq={idx}",
        )

    # ----------------------------------------------
    # Start / end markers
    # ----------------------------------------------
    folium.Marker(
        location=[group["start_point"]["lat"], group["start_point"]["lon"]],
        icon=folium.Icon(color="green", icon="play"),
        popup="Group start",
    ).add_to(m)

    folium.Marker(
        location=[group["end_point"]["lat"], group["end_point"]["lon"]],
        icon=folium.Icon(color="purple", icon="stop"),
        popup="Group end",
    ).add_to(m)

    # ----------------------------------------------
    # Save map
    # ----------------------------------------------
    out_dir = _ensure_output_dir()

    if filename is None:
        filename = f"grouped_segment_{group['seg_seq_id']}.html"

    out_path = out_dir / filename
    m.save(out_path)

    return out_path

if __name__ == "__main__":
    client = OSMSegmentClient(
        base_url="local",
        input_crs="EPSG:4326",
        output_crs="EPSG:4326",
        allowed_highways=[
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "living_street",
        ],
    )
    points = [
        {"lon": 14.7110, "lat": 55.1225},  # Nordskovvej 3
        {"lon": 14.7107, "lat": 55.1225},  # Nordskovvej 1
        {"lon": 14.7104, "lat": 55.1223},  # Nordskovvej 2A
    ]
    segments = client.snap_nearest_batch(points,
                                            x_key="lon",
                                            y_key="lat")
    seg = segments[0]
    group = client.group_segments_on_side(
        seg,
        allowed_highways=[
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "living_street",
        ],
        use_rotated_side=False
    )
    path = plot_segment_group(seg=seg, group=group)
    print(f"Map written to: {path}")