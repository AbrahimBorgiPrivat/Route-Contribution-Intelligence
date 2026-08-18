/**
 * Generic legend panel for route + marker layers.
 * Renders colored lines and icons directly in the DOM.
 */

import { ROUTE_COLORS, MARKER_COLORS } from "./map_layers.js";

export function addCustomLegend(map) {
    const legend = L.control({ position: "topright" });

    legend.onAdd = function () {
        const div = L.DomUtil.create("div", "fk-legend");

        div.innerHTML = `
            <div class="legend-section">
                <strong>Routes</strong>
                ${renderRouteLegend()}
            </div>
            <div class="legend-section">
                <strong>Markers</strong>
                ${renderMarkerLegend()}
            </div>
        `;

        return div;
    };

    legend.addTo(map);
}

function renderRouteLegend() {
    return Object.entries(ROUTE_COLORS).map(([name, color]) => `
        <div class="legend-row" data-layer="${name}">
            <span class="legend-line" style="background:${color}"></span>
            ${name}
        </div>
    `).join("");
}

function renderMarkerLegend() {
    return Object.entries(MARKER_COLORS).map(([name, color]) => `
        <div class="legend-row" data-layer="${name}">
            <svg width="14" height="14" style="margin-right:6px;">
                <circle cx="7" cy="7" r="6" fill="${color}"/>
            </svg>
            ${name}
        </div>
    `).join("");
}
