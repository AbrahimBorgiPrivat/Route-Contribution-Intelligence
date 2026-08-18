export async function loadRouteJson(relativePath) {
    const res = await fetch(`../data/${relativePath}`);
    if (!res.ok) throw new Error(`Failed to load ${relativePath}`);
    return await res.json();
}