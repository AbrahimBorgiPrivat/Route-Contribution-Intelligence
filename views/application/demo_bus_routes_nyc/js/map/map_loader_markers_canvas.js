import { MARKER_LAYERS, MARKER_COLORS } from "./map_layers.js";
import { fetchGeoJSON } from "../data/fetch_geojson.js";

/**
 * Canvas-based marker loader for large marker sets.
 * Intended for overview / index maps.
 */
export async function loadMarkerGeoJSONCanvas(
    url,
    accumulator,
    renderer,
    options = {}
) {
    const { onLayerCreated = null } = options;

    const geo = await fetchGeoJSON(url);
    geo.features.forEach(f => {
        if (!f.geometry || f.geometry.type !== "Point") return;
        const [lon, lat] = f.geometry.coordinates;
        const props = f.properties || {};
        const layerName = props.layer;
        const color = MARKER_COLORS[layerName] || "#666";
        const marker = L.circleMarker([lat, lon], {
            radius: 5,
            fillColor: color,
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.9,
            renderer
        });
        if (props.label) {
            marker.bindTooltip(props.label, {
                direction: "top",
                offset: [0, -6],
                opacity: 0.9
            });
        }
        const popupHtml = `
            <strong>Route:</strong> ${props.route_id ?? ""}<br>
            <strong>Route no.:</strong> ${props.number ?? ""}<br>
            <strong>Stops:</strong> ${props.postboxes ?? ""}<br>
            <strong>Revenue:</strong> ${formatNumber(props.revenue)}<br>
            <strong>Address:</strong> ${props.address ?? ""}
        `;
        marker.bindPopup(popupHtml);
        MARKER_LAYERS[layerName].addLayer(marker);
        accumulator.push(marker);
        onLayerCreated?.(marker, layerName);
    });
}

function formatNumber(val) {
    if (val === null || val === undefined) return "";
    return Number(val).toLocaleString("en-US", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}
