export function formatTransportform(value) {
    const raw = value?.toString().trim();
    if (!raw) return "-";

    const normalized = raw.toLowerCase();
    const labels = {
        foot: "Gang",
        walk: "Gang",
        walking: "Gang",
        bike: "Cykel",
        bicycle: "Cykel",
        cycling: "Cykel",
        car: "Bil",
        drive: "Bil",
        driving: "Bil"
    };

    return labels[normalized] ?? raw;
}
