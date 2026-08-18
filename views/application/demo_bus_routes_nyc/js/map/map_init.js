import { createMapBaseLayers } from "./map_style_selector.js";

/**
 * Initialize a Leaflet map with switchable base layers.
 */
export function initMap(containerId, center = [55.0, 12.0], zoom = 10) {
    const map = L.map(containerId);
    const baseLayers = createMapBaseLayers();

    baseLayers.color.addTo(map);
    map._fkBaseLayers = baseLayers;
    map._fkActiveBaseLayer = "color";

    map.setView(center, zoom);
    return map;
}
