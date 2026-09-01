import { createMapBaseLayer, setMapStyle } from "./map_style_selector.js";

/**
 * Initialize a Leaflet map with switchable base layers.
 */
export function initMap(containerId, center = [55.0, 12.0], zoom = 10) {
    const map = L.map(containerId);
    const baseLayer = createMapBaseLayer();

    baseLayer.addTo(map);
    map._fkBaseLayer = baseLayer;
    setMapStyle(map, "color");

    map.setView(center, zoom);
    return map;
}
