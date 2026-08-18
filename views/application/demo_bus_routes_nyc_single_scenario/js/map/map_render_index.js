/**
 * High-level renderer for the INDEX PAGE combined map.
 */

import { initMap } from "./map_init.js";
import { loadRouteGeoJSON } from "./map_loader_routes.js";
import { loadMarkerGeoJSONCanvas } from "./map_loader_markers_canvas.js";
import { fitMapToLayers } from "./map_fit.js";
import { addCustomLegend } from "./map_legend_custom.js";
import { ROUTE_LAYERS, MARKER_LAYERS } from "./map_layers.js";
import { initRouteTypeSelector } from "./map_type_selector.js";
import { loadMultipleRoutes } from "./map_load_multiple_routes.js";

export async function renderIndexMap(containerId, routes) {
    const map = initMap(containerId);
    const allLayers = [];
    const canvasRenderer = L.canvas({ padding: 0.5 });
    await loadMultipleRoutes(routes, {
        loadRoute: async (routeData) => {
            const base = `../data/routes/${routeData.route_id}`;
            await loadRouteGeoJSON(
                `${base}/${routeData.geojson_route}`,
                allLayers,
                map,
                {
                    arrows: false,              // no arrows
                    renderer: canvasRenderer   // canvas routes
                }
            );
        },
        loadMarkers: async (routeData) => {
            const base = `../data/routes/${routeData.route_id}`;
            await loadMarkerGeoJSONCanvas(
                `${base}/${routeData.geojson_markers}`,
                allLayers,
                canvasRenderer
            );
        }
    });
    Object.values(ROUTE_LAYERS).forEach(layer => layer.addTo(map));
    Object.values(MARKER_LAYERS).forEach(layer => layer.addTo(map));
    fitMapToLayers(map, allLayers);
    L.control.layers(
        null,
        {
            "T1 Original": ROUTE_LAYERS["T1 Original"],
            "T1 Optimal": ROUTE_LAYERS["T1 Optimal"],
            "T2 Original": ROUTE_LAYERS["T2 Original"],
            "T2 Optimal": ROUTE_LAYERS["T2 Optimal"],
            "T1 Normal": MARKER_LAYERS["T1 Normal"],
            "T1 Outlier": MARKER_LAYERS["T1 Outlier"],
            "T1 Significant": MARKER_LAYERS["T1 Significant"],
            "T2 Normal": MARKER_LAYERS["T2 Normal"],
            "T2 Outlier": MARKER_LAYERS["T2 Outlier"],
            "T2 Significant": MARKER_LAYERS["T2 Significant"]
        },
        { collapsed: false }
    ).addTo(map);
    setTimeout(() => map.invalidateSize(), 50);
    initRouteTypeSelector(map);
    map.on("overlayadd", function (e) {
        const row = document.querySelector(`.fk-legend [data-layer="${e.name}"]`);
        if (row) row.style.display = "flex";
    });
    map.on("overlayremove", function (e) {
        const row = document.querySelector(`.fk-legend [data-layer="${e.name}"]`);
        if (row) row.style.display = "none";
    });
    addCustomLegend(map);
    return map;
}
