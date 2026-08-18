/**
 * Generic helper to load multiple routes (routes + markers) in parallel.
 * Reusable for index maps, dashboards, etc.
 */

import { fetchRoute } from "../data/fetch_route.js";
export async function loadMultipleRoutes(routes, { loadRoute, loadMarkers }) {
    await Promise.all(
        routes.map(async (r) => {
            const routeData = await fetchRoute(r.route_id);
            if (loadRoute) {
                await loadRoute(routeData);
            }
            if (loadMarkers) {
                await loadMarkers(routeData);
            }
        })
    );
}