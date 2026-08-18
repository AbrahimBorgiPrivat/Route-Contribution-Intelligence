import { initMap } from "./map_init.js";
import { loadRouteGeoJSON } from "./map_loader_routes.js";
import { loadMarkerGeoJSONCanvas } from "./map_loader_markers_canvas.js";
import { fitMapToLayers } from "./map_fit.js";
import { addCustomLegend } from "./map_legend_custom.js";
import { ROUTE_LAYERS, MARKER_LAYERS } from "./map_layers.js";
import { initRouteTypeSelector } from "./map_type_selector.js";
import { loadMultipleRoutesV2 } from "./map_load_multiple_routes_v2.js";
import { addMapStyleSelector } from "./map_style_selector.js";

export async function renderIndexMap(containerId, scenarioRoutes) {
    const map = initMap(containerId);
    addMapStyleSelector(map, containerId);
    const allLayers = [];
    const layerRegistry = [];
    const canvasRenderer = L.canvas({ padding: 0.5 });
    await loadMultipleRoutesV2(scenarioRoutes, {
        loadRoute: async (routeGeoURL, routeMeta) => {
            await loadRouteGeoJSON(
                routeGeoURL,
                allLayers,
                map,
                {
                    arrows: false,
                    renderer: canvasRenderer,
                    onLayerCreated: (layer, layerName) => {
                        layerRegistry.push({
                            layer,
                            group: ROUTE_LAYERS[layerName],
                            routeId: String(routeMeta.route_id),
                            transportform: routeMeta.transportform ?? "-"
                        });
                    }
                }
            );
        },
        loadMarkers: async (markerGeoURL, routeMeta) => {
            await loadMarkerGeoJSONCanvas(
                markerGeoURL,
                allLayers,
                canvasRenderer,
                {
                    onLayerCreated: (layer, layerName) => {
                        layerRegistry.push({
                            layer,
                            group: MARKER_LAYERS[layerName],
                            routeId: String(routeMeta.route_id),
                            transportform: routeMeta.transportform ?? "-"
                        });
                    }
                }
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
        const row = document.querySelector(
            `.fk-legend [data-layer="${e.name}"]`
        );
        if (row) row.style.display = "flex";
    });
    map.on("overlayremove", function (e) {
        const row = document.querySelector(
            `.fk-legend [data-layer="${e.name}"]`
        );
        if (row) row.style.display = "none";
    });
    addCustomLegend(map);
    return {
        map,
        applyFilters({
            transportforms = [],
            routes = []
        } = {}) {
            const transportSet = new Set(transportforms);
            const routeSet = new Set(routes.map(String));

            layerRegistry.forEach(record => {
                const isVisible =
                    (transportSet.size === 0
                        || transportSet.has(record.transportform))
                    && (routeSet.size === 0
                        || routeSet.has(record.routeId));

                const hasLayer = record.group.hasLayer(record.layer);

                if (isVisible && !hasLayer) {
                    record.group.addLayer(record.layer);
                }

                if (!isVisible && hasLayer) {
                    record.group.removeLayer(record.layer);
                }
            });
        }
    };
}
