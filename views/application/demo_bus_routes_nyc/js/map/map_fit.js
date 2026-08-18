/**
 * Fit the map to cover all route + marker layers.
 */
export function fitMapToLayers(map, layers) {
    if (!layers.length) return;
    const fg = L.featureGroup(layers);
    map.fitBounds(fg.getBounds(), { padding: [30, 30] });
    setTimeout(() => map.invalidateSize(), 150);
}
