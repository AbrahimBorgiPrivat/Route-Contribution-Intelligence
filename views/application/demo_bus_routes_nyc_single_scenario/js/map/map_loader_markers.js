import { MARKER_LAYERS, MARKER_COLORS } from "./map_layers.js";
import { fetchGeoJSON } from "../data/fetch_geojson.js";

/**
 * Load marker GeoJSON and add each point to the correct marker layer group.
 * Used on route pages.
 */
export async function loadMarkerGeoJSON(url, accumulator) {
    const geo = await fetchGeoJSON(url);
    geo.features.forEach(f => {
        if (!f.geometry || f.geometry.type !== "Point") return;
        const [lon, lat] = f.geometry.coordinates;
        const props = f.properties || {};
        const layerName = props.layer;
        const number = props.number ?? "";
        const color = MARKER_COLORS[layerName] || "#666";
        const icon = L.divIcon({
            className: "custom-marker",
            html: `
                <svg width="26" height="26" viewBox="0 0 26 26">
                    <circle cx="13" cy="13" r="12"
                        fill="${color}"
                        stroke="black"
                        stroke-width="1.5" />
                    <text x="13" y="17"
                        text-anchor="middle"
                        font-size="8px"
                        font-weight="700"
                        fill="white"
                        font-family="Inter, sans-serif">
                        ${number}
                    </text>
                </svg>
            `,
            iconSize: [26, 26],
            iconAnchor: [13, 26]
        });

        const popupHtml = `
            <strong>Route:</strong> ${props.route_id ?? ""}<br>
            <strong>Route no.:</strong> ${props.number ?? ""}<br>
            <strong>Stops:</strong> ${props.postboxes ?? ""}<br>
            <strong>Revenue:</strong> ${formatNumber(props.revenue)}<br>
            <strong>Address:</strong> ${props.address ?? ""}
        `;

        const marker = L.marker([lat, lon], { icon }).bindPopup(popupHtml);

        MARKER_LAYERS[layerName].addLayer(marker);
        accumulator.push(marker);
    });
}

function formatNumber(val) {
    if (val === null || val === undefined) return "";
    return Number(val).toLocaleString("en-US", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}
