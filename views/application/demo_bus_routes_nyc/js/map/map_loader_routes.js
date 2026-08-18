/**
 * Load route GeoJSON and add each feature to the correct route layer group.
 */

import { ROUTE_LAYERS, ROUTE_COLORS } from "./map_layers.js";
import { fetchGeoJSON } from "../data/fetch_geojson.js";
import { addPolylineArrows } from "./map_arrows.js";   // ← IMPORTANT

export async function loadRouteGeoJSON(url, accumulator, map, options = {}) {
    const {
        arrows = true,
        reverseArrows = false,
        renderer = null,
        onLayerCreated = null
    } = options;
    const geo = await fetchGeoJSON(url);
    geo.features.forEach(f => {
        if (!f.geometry || f.geometry.type !== "LineString") return;
        const coords = f.geometry.coordinates;
        if (!Array.isArray(coords) || coords.length < 2) {
            console.warn("Skipping LineString with < 2 points:", coords);
            return;
        }
        const layerName = f.properties.layer || "T1 Original";
        const color = ROUTE_COLORS[layerName] || "#444";
        const latlngs = coords
            .map(c => {
                if (!Array.isArray(c) || c.length < 2) return null;
                return [c[1], c[0]];
            })
            .filter(Boolean);
        if (latlngs.length < 2) {
            console.warn("Skipping LineString after cleaning:", latlngs);
            return;
        }
        const poly = L.polyline(latlngs, {
            color,
            weight: 4,
            opacity: 0.9,
            renderer
        });
        if (arrows) {
            addPolylineArrows(map, poly, {
                color,
                size: 10,
                gap: 20,
                reverse: reverseArrows
            });
        }
        ROUTE_LAYERS[layerName].addLayer(poly);
        accumulator.push(poly);
        onLayerCreated?.(poly, layerName);
    });
}
