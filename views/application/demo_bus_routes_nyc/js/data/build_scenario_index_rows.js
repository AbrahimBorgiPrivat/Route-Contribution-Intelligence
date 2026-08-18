import { loadRouteJsonCached } from "./load_route_json_cached.js";
import { extractRouteKPIsV2 } from "./extract_route_kpis_v2.js";
import { aggregateKPIs } from "./aggregate_kpis.js";

const ROUTE_KPI_CACHE = new Map();
const ROUTE_LOAD_CONCURRENCY = 24;

export async function buildScenarioIndexRows(entries) {
    const groups = groupScenarioEntries(entries);
    const rows = [];

    for (const group of groups) {
        const routeKPIs = await loadRouteKPIs(group.routeJsonPaths);
        rows.push({
            apr_profile: group.apr_profile,
            label: group.label,
            t1: projectTypeMetrics(routeKPIs, true),
            t2: projectTypeMetrics(routeKPIs, false),
        });
    }

    return rows;
}

function groupScenarioEntries(entries) {
    const groups = new Map();

    entries.forEach(entry => {
        const key = `${entry.APR_profile}__${entry.label}`;
        if (!groups.has(key)) {
            groups.set(key, {
                apr_profile: entry.APR_profile,
                label: entry.label,
                routeJsonPaths: [],
            });
        }

        groups.get(key).routeJsonPaths.push(entry.route_json);
    });

    return [...groups.values()];
}

async function loadRouteKPIs(routeJsonPaths) {
    return mapWithConcurrency(
        routeJsonPaths,
        ROUTE_LOAD_CONCURRENCY,
        loadRouteKPI
    );
}

function loadRouteKPI(routeJsonPath) {
    if (!ROUTE_KPI_CACHE.has(routeJsonPath)) {
        ROUTE_KPI_CACHE.set(
            routeJsonPath,
            loadRouteJsonCached(routeJsonPath).then(extractRouteKPIsV2)
        );
    }

    return ROUTE_KPI_CACHE.get(routeJsonPath);
}

function projectTypeMetrics(routeKPIs, strictOrder) {
    const aggregate = aggregateKPIs(routeKPIs, strictOrder);
    return {
        DG_original: aggregate.DG_original,
        DG_best: aggregate.DG_best,
        revenue_original: aggregate.revenue_original,
        revenue_best: aggregate.revenue_best,
        expense_original: aggregate.expense_original,
        expense_best: aggregate.expense_best,
        seg_outliers: aggregate.seg_outliers,
    };
}

async function mapWithConcurrency(items, concurrency, mapper) {
    const results = new Array(items.length);
    let currentIndex = 0;

    async function worker() {
        while (currentIndex < items.length) {
            const index = currentIndex;
            currentIndex += 1;
            results[index] = await mapper(items[index]);
        }
    }

    const workerCount = Math.min(concurrency, items.length);
    await Promise.all(
        Array.from({ length: workerCount }, () => worker())
    );

    return results;
}
