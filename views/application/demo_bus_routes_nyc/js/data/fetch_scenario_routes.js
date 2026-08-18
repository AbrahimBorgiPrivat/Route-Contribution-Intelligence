import { loadRegistry } from "./load_registry.js";
import { loadScenarioMetadata } from "./load_scenario_metadata.js";

export async function fetchScenarioRoutes(label, apr, week) {
    const [registry, metadata] = await Promise.all([
        loadRegistry(),
        loadScenarioMetadata(),
    ]);

    const scenarioRoutes = registry.filter(r =>
        r.label === label &&
        r.APR_profile === apr &&
        r.Week_Profile === week
    );

    if (!scenarioRoutes.length) {
        console.warn("No routes found for scenario");
    }

    const routeJsons = await Promise.all(
        scenarioRoutes.map(r =>
            fetch(`../data/${r.route_json}`).then(res => {
                if (!res.ok) {
                    throw new Error(`Failed loading ${r.route_json}`);
                }
                return res.json();
            })
        )
    );

    return {
        routes: scenarioRoutes,
        routeJsons,
        metadata,
    };
}
