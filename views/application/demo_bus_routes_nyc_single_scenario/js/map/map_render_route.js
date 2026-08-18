/**
 * High-level renderer for a single route page.
 * Loads route lines, markers, fits the map, and attaches custom FK legend.
 */

import { initMap } from "./map_init.js";
import { initRouteTypeSelector } from "./map_type_selector.js";
import { loadRouteGeoJSON } from "./map_loader_routes.js";
import { loadMarkerGeoJSON } from "./map_loader_markers.js";
import { fitMapToLayers } from "./map_fit.js";
import { addCustomLegend } from "./map_legend_custom.js";
import { ROUTE_LAYERS, MARKER_LAYERS } from "./map_layers.js";

export async function renderRouteMap(containerId, routeConfig) {

    const map = initMap(containerId);
    const allLayers = [];

    // Load geometry (route lines use map for arrow rendering)
    await loadRouteGeoJSON(routeConfig.routeGeoURL, allLayers, map);
    await loadMarkerGeoJSON(routeConfig.markerGeoURL, allLayers);

    // Make all layers visible by default
    Object.values(ROUTE_LAYERS).forEach(layer => layer.addTo(map));
    Object.values(MARKER_LAYERS).forEach(layer => layer.addTo(map));

    // Fit map view
    fitMapToLayers(map, allLayers);

    // Add layer selector (checkbox toggle)
    L.control.layers(
        null,
        {
            // ROUTES
            "T1 Original": ROUTE_LAYERS["T1 Original"],
            "T1 Optimal":  ROUTE_LAYERS["T1 Optimal"],
            "T2 Original": ROUTE_LAYERS["T2 Original"],
            "T2 Optimal":  ROUTE_LAYERS["T2 Optimal"],

            // MARKERS
            "T1 Normal":       MARKER_LAYERS["T1 Normal"],
            "T1 Outlier":      MARKER_LAYERS["T1 Outlier"],
            "T1 Significant":  MARKER_LAYERS["T1 Significant"],
            "T2 Normal":       MARKER_LAYERS["T2 Normal"],
            "T2 Outlier":      MARKER_LAYERS["T2 Outlier"],
            "T2 Significant":  MARKER_LAYERS["T2 Significant"]
        },
        { collapsed: false }
    ).addTo(map);

    setTimeout(() => map.invalidateSize(), 50);

    initRouteTypeSelector(map);
    // Make FK legend responsive (sync with toggles)
    map.on("overlayadd", function(e) {
        const row = document.querySelector(`.fk-legend [data-layer="${e.name}"]`);
        if (row) row.style.display = "flex";
    });

    map.on("overlayremove", function(e) {
        const row = document.querySelector(`.fk-legend [data-layer="${e.name}"]`);
        if (row) row.style.display = "none";
    });

    // Add visual FK legend
    addCustomLegend(map);

    return map;
}