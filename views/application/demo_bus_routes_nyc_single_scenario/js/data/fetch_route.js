/**
 * Load a single route's metadata JSON.
 */
export async function fetchRoute(routeId) {
    const url = `../data/routes/${routeId}/${routeId}.json`;
    return fetch(url).then(r => r.json());
}