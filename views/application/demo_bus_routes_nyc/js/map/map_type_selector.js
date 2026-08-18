/**
 * Handles switching between Type 1, Type 2, or Both layers.
 */

import { ROUTE_LAYERS, MARKER_LAYERS } from "./map_layers.js";

export function initRouteTypeSelector(map) {
    const btns = document.querySelectorAll(".route-type-selector button");
    btns.forEach(btn => {
        btn.addEventListener("click", () => {
            btns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const type = btn.dataset.type;
            toggleLayers(map, type);
        });
    });
}

function toggleLayers(map, type) {
    const t1Layers = [
        ROUTE_LAYERS["T1 Original"],
        ROUTE_LAYERS["T1 Optimal"],
        MARKER_LAYERS["T1 Normal"],
        MARKER_LAYERS["T1 Outlier"],
        MARKER_LAYERS["T1 Significant"]
    ];
    const t2Layers = [
        ROUTE_LAYERS["T2 Original"],
        ROUTE_LAYERS["T2 Optimal"],
        MARKER_LAYERS["T2 Normal"],
        MARKER_LAYERS["T2 Outlier"],
        MARKER_LAYERS["T2 Significant"]
    ];
    [...t1Layers, ...t2Layers].forEach(l => map.removeLayer(l));
    if (type === "t1") {
        t1Layers.forEach(l => map.addLayer(l));
    } else if (type === "t2") {
        t2Layers.forEach(l => map.addLayer(l));
    } else {
        [...t1Layers, ...t2Layers].forEach(l => map.addLayer(l));
    }
}
