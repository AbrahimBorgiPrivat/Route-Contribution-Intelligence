/**
 * Fetch any GeoJSON file and return the parsed JSON object.
 */
export async function fetchGeoJSON(url) {
    return fetch(url).then(r => r.json());
}
