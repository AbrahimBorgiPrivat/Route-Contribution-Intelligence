/**
 * Load the index file that contains the list of all routes.
 */
export async function fetchRoutesIndex() {
    return fetch("../data/routes_index.json").then(r => r.json());
}