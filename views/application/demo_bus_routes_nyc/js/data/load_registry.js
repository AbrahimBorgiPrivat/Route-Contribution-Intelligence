export async function loadRegistry() {
    const res = await fetch("../data/registry.json");
    if (!res.ok) throw new Error("Failed to load registry.json");
    return await res.json();
}
