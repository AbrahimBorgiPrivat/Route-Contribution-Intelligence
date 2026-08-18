export async function loadMultipleRoutesV2(routes, { loadRoute, loadMarkers }) {

    await Promise.all(
        routes.map(async (route) => {

            const basePath =
                `../data/${route.route_json.replace(`/${route.route_id}.json`, "")}`;

            const routeGeo = `${basePath}/${route.route_id}_route.geojson`;
            const markerGeo = `${basePath}/${route.route_id}_markers.geojson`;

            if (loadRoute) {
                await loadRoute(routeGeo, route);
            }

            if (loadMarkers) {
                await loadMarkers(markerGeo, route);
            }
        })
    );
}
