const EMPTY_SCENARIO_METADATA = Object.freeze({
    labels: {},
    APR_profiles: {},
    week_profiles: {},
});

export async function loadScenarioMetadata() {
    try {
        const res = await fetch("../data/scenario_metadata.json");
        if (!res.ok) {
            return EMPTY_SCENARIO_METADATA;
        }

        const data = await res.json();
        return {
            labels: data?.labels ?? {},
            APR_profiles: data?.APR_profiles ?? {},
            week_profiles: data?.week_profiles ?? {},
        };
    } catch (_) {
        return EMPTY_SCENARIO_METADATA;
    }
}

export function getScenarioExplanation(metadata, type, key) {
    if (!metadata || !key) {
        return null;
    }
    const mapping = metadata[type];
    if (!mapping || typeof mapping !== "object") {
        return null;
    }
    const explanation = mapping[key];
    return typeof explanation === "string" && explanation.trim()
        ? explanation.trim()
        : null;
}
