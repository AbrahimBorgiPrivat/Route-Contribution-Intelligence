/**
 * Aggregate KPIs across all routes for a given solution type.
 * strictOrder = true  → Type 1
 * strictOrder = false → Type 2
 */

export function aggregateKPIs(routeKPIs, strictOrder) {
    const prefix = strictOrder ? "t1" : "t2";

    let DG_original = 0;
    let DG_best = 0;
    let seg_outliers = 0;
    let optimal_routes = 0;

    for (const r of routeKPIs) {
        const dgOrg = r[`${prefix}_DG_original`];
        const dgBest = r[`${prefix}_DG_best`];
        const outliers = r[`${prefix}_seg_outliers`];

        if (dgOrg === "-" || dgBest === "-") continue;

        DG_original += Number(String(dgOrg).replace(/[^\d.-]/g, ""));
        DG_best += Number(String(dgBest).replace(/[^\d.-]/g, ""));
        seg_outliers += Number(outliers);

        if (Number(outliers) === 0) {
            optimal_routes += 1;
        }
    }

    return {
        DG_original,
        DG_best,
        seg_outliers,
        optimal_routes
    };
}
