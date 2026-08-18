/**
 * Initialize a Leaflet map with OSM tiles.
 */
export function initMap(containerId, center = [55.0, 12.0], zoom = 10) {
    const map = L.map(containerId);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19
    }).addTo(map);
    map.setView(center, zoom);
    return map;
}
