/**
 * Get a single query parameter from the current URL.
 * Returns null if not present.
 */
export function getQueryParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}

/**
 * Get all query parameters as a plain object.
 */
export function getAllQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const out = {};
    for (const [key, val] of params.entries()) {
        out[key] = val;
    }
    return out;
}
