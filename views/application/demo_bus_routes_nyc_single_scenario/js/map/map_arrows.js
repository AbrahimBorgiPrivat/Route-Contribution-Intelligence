/**
 * Adds clean, Folium-style arrows along a polyline.
 * Much clearer, smaller, and spaced so they do not overlap.
 */

export function addPolylineArrows(map, polyline, options = {}) {

    const color = options.color || polyline.options.color || "#000";
    const size  = options.size  || 8;     // arrowhead size
    const gap   = options.gap   || 50;    // distance between arrows

    const arrowLayer = L.layerGroup().addTo(map);

    function render() {

        arrowLayer.clearLayers();

        const latlngs = polyline.getLatLngs();
        if (!Array.isArray(latlngs) || latlngs.length < 2) return;

        for (let i = 1; i < latlngs.length; i++) {

            const p1 = map.latLngToLayerPoint(latlngs[i - 1]);
            const p2 = map.latLngToLayerPoint(latlngs[i]);

            const segmentLength = p1.distanceTo(p2);
            const count = Math.floor(segmentLength / gap);

            const dx = (p2.x - p1.x) / segmentLength;
            const dy = (p2.y - p1.y) / segmentLength;

            for (let k = 1; k <= count; k++) {

                const px = p1.x + dx * (k * gap);
                const py = p1.y + dy * (k * gap);

                const center = map.layerPointToLatLng([px, py]);

                const angle = Math.atan2(dy, dx) * (180 / Math.PI);

                // Construct a clean triangular arrowhead
                const arrow = L.polygon([
                    map.layerPointToLatLng([
                        px, 
                        py
                    ]),
                    map.layerPointToLatLng([
                        px - size * Math.cos((angle - 160) * Math.PI / 180),
                        py - size * Math.sin((angle - 160) * Math.PI / 180)
                    ]),
                    map.layerPointToLatLng([
                        px - size * Math.cos((angle + 160) * Math.PI / 180),
                        py - size * Math.sin((angle + 160) * Math.PI / 180)
                    ])
                ], {
                    fillColor: color,
                    fillOpacity: 1.0,
                    weight: 1.5,
                    color: "black",       
                    opacity: 0.9
                });

                arrowLayer.addLayer(arrow);
            }
        }
    }

    // Re-render on zoom/move
    map.on("zoomend moveend", render);
    render();

    // Keep arrows synchronized with route layer
    polyline.on("remove", () => map.removeLayer(arrowLayer));
    polyline.on("add", () => arrowLayer.addTo(map));
}
