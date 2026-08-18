import { loadRouteJson } from "./load_route_json.js";

const ROUTE_JSON_CACHE = new Map();

export function loadRouteJsonCached(relativePath) {
    if (!ROUTE_JSON_CACHE.has(relativePath)) {
        ROUTE_JSON_CACHE.set(relativePath, loadRouteJson(relativePath));
    }

    return ROUTE_JSON_CACHE.get(relativePath);
}
