import folium
from folium import LayerControl
from folium.map import Marker
from folium.features import DivIcon
from folium.vector_layers import PolyLine
from folium.plugins import PolyLineTextPath
import polyline
import tempfile
import webbrowser
import os
from typing import List, Dict, Any, Optional

class RoutePlotterFolium:
    """
    Modular Folium plotter for Identifying Economic Outliers in Routing Networks.
    Supports:
        - multiple route layers
        - multiple point layers
        - outlier highlighting (added later)
        - saving or returning map
    """
    def __init__(self, tiles="OpenStreetMap", zoom_start=16):
        self.tiles = tiles
        self.zoom_start = zoom_start
        self.map = None
        self.initialized = False
        self.center = None
        self.feature_groups = []     # <--- ADD THIS

    def init_map(self, lat: float, lon: float) -> None:
        """Initialize map once."""
        self.center = (lat, lon)
        self.map = folium.Map(
            location=self.center,
            tiles=self.tiles,
            zoom_start=self.zoom_start,
        )
        self.initialized = True

    @staticmethod
    def decode_steps(steps) -> List[tuple[float, float]]:
        """Decode OSRM polyline steps into coordinates."""
        coords: List[tuple[float, float]] = []
        for step in steps:
            pts = polyline.decode(step["geometry"])
            coords.extend(pts)
        return coords

    def add_route_from_steps(
        self,
        steps_list,
        name: str = "Route",
        color: str = "black",
        weight: int = 3,
    ) -> None:
        """
        steps_list: list of OSRM legs, each containing steps with encoded geometry.
        """
        full_coords: List[tuple[float, float]] = []
        for leg_steps in steps_list:
            full_coords.extend(self.decode_steps(leg_steps))
        if not full_coords:
            return
        if not self.initialized:
            lat0, lon0 = full_coords[0]
            self.init_map(lat0, lon0)
        fg = folium.FeatureGroup(name=name, overlay=True, control=True)
        pl = folium.PolyLine(
            full_coords,
            color=color,
            weight=weight,
            opacity=0.6,
        ).add_to(fg)
        PolyLineTextPath(
            pl,
            ">    ",  
            repeat=True,
            offset=8,
            attributes={
                "font-size": "12px",
                "fill": "none",
                "stroke": color,
                "stroke-width": "1.5px",
            },
        ).add_to(fg)
        fg.add_to(self.map)
        self.feature_groups.append(fg) 

    def add_points(
        self,
        locations: List[Dict[str, Any]],
        labels: Optional[List[Any]] = None,
        name: str = "Addresses",
        color: str = "orange"
    ) -> None:
        """
        Add labeled point markers to the map.
        ----------
        locations : List of location dicts. Each dict MUST contain:
                - "lat": float or convertible to float (latitude)
                - "lon": float or convertible to float (longitude)
        labels : Labels to show on markers. Must be same length as `locations`.
                 If None → uses [0, 1, 2, ...].
        name : Layer name used in folium.
        color : Marker background color.
        """
        if labels is None:
            labels = list(range(len(locations)))
        if not self.initialized:
            lat0 = float(locations[0]["lat"])
            lon0 = float(locations[0]["lon"])
            self.init_map(lat0, lon0)
        fg = folium.FeatureGroup(name=name, overlay=True, control=True)
        for loc, label in zip(locations, labels):
            lat = float(loc["lat"])
            lon = float(loc["lon"])
            popup_html = self._build_point_popup_html(loc)
            html = f"""
                <div style="
                    background-color:{color};
                    color:white;
                    border-radius:50%;
                    width:28px;
                    height:28px;
                    text-align:center;
                    line-height:28px;
                    font-weight:bold;
                    border:2px solid black;
                ">{label}</div>
            """
            marker = folium.Marker(
                (lat, lon),
                icon=DivIcon(icon_size=(32, 32), html=html),
                tooltip=f"Address {label}",
            )
            if popup_html:
                marker.add_child(folium.Popup(popup_html, max_width=320))
            fg.add_child(marker)
        fg.add_to(self.map)
        self.feature_groups.append(fg)

    @staticmethod
    def _build_point_popup_html(loc: Dict[str, Any]) -> Optional[str]:
        route_name = loc.get("route_id")
        stop_name = loc.get("address")

        rows = []
        if route_name not in (None, ""):
            rows.append(
                f"<div><strong>Rutenavn:</strong> {route_name}</div>"
            )
        if stop_name not in (None, ""):
            rows.append(
                f"<div><strong>Stopnavn:</strong> {stop_name}</div>"
            )

        if not rows:
            return None

        return (
            '<div style="font-family: Inter, Arial, sans-serif; '
            'font-size: 13px; line-height: 1.45;">'
            + "".join(rows)
            + "</div>"
        )
    
    def add_layer_control(self) -> None:
        """Add layer toggler."""
        LayerControl().add_to(self.map)

    def create_feature_group(self, name):
        fg = folium.FeatureGroup(name=name, overlay=True, control=True)
        return fg

    def add_feature_group(self, fg):
        fg.add_to(self.map)
        self.feature_groups.append(fg)
    
    def clone_child(self, child):
        """Clone supported Folium map elements so they can be moved across maps."""
        if isinstance(child, Marker):
            icon = child.icon
            if isinstance(icon, DivIcon):
                return Marker(
                    location=child.location,
                    icon=DivIcon(
                        icon_size=icon.options.get("icon_size"),
                        icon_anchor=icon.options.get("icon_anchor"),
                        html=icon.options.get("html")
                    ),
                    tooltip=child.options.get("tooltip"),
                    popup=child._children.get(next(
                        (key for key, value in child._children.items()
                         if value.__class__.__name__ == "Popup"),
                        None
                    )) if child._children else None
                )
            return Marker(
                location=child.location,
                icon=icon,
                tooltip=child.options.get("tooltip"),
                popup=child._children.get(next(
                    (key for key, value in child._children.items()
                     if value.__class__.__name__ == "Popup"),
                    None
                )) if child._children else None
            )
        if isinstance(child, PolyLine):
            return PolyLine(
                locations=child.locations,
                color=child.options.get("color"),
                weight=child.options.get("weight"),
                opacity=child.options.get("opacity"),
            )
        return None
    
    def save_map(self, file_path="map.html"):
        """Save map to file and return path."""
        if not self.initialized:
            raise RuntimeError("Map not initialized. Add a route or point layer first.")

        self.map.save(file_path)
        return file_path

    def show_map(self):
        """Save to temporary file and open in browser."""
        if not self.initialized:
            raise RuntimeError("Map not initialized.")

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            filepath = f.name

        self.map.save(filepath)
        webbrowser.open("file://" + os.path.abspath(filepath))
