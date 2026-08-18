export function aggregateKPIs(routeKPIs, strictOrder) {

    const prefix = strictOrder ? "t1" : "t2";

    let DG_original = 0;
    let DG_best = 0;
    let seg_outliers = 0;
    let optimal_routes = 0;
    let routes = 0;
    let L_original_m = 0;
    let L_opt_m = 0;
    let L_original_sec = 0;
    let L_opt_sec = 0;
    let expense_original = 0;
    let expense_best = 0;
    let revenue_original = 0;
    let revenue_best = 0;
    let addresses_original = 0;
    let addresses_best = 0;

    for (const r of routeKPIs) {

        const DG_org = Number(r[`${prefix}_DG_original`]) || 0;
        const DG_best_val = Number(r[`${prefix}_DG_best`]) || 0;
        const outliers = Number(r[`${prefix}_seg_outliers`]) || 0;
        const L_original = Number(r[`${prefix}_L_original`]) || 0;
        const L_opt = Number(r[`${prefix}_L_opt`]) || 0;
        const unit = r[`${prefix}_unit`];
        const expenseOrg = Number(r[`${prefix}_expense_original`]) || 0;
        const expenseBest = Number(r[`${prefix}_expense_best`]) || 0;
        const revenueOrg = Number(r[`${prefix}_revenue_original`]) || 0;
        const revenueBest = Number(r[`${prefix}_revenue_best`]) || 0;
        const addressesOrg = Number(r[`${prefix}_addresses_original`]) || 0;
        const addressesBest = Number(r[`${prefix}_addresses_best`]) || 0;

        DG_original += DG_org;
        DG_best += DG_best_val;
        expense_original += expenseOrg;
        expense_best += expenseBest;
        revenue_original += revenueOrg;
        revenue_best += revenueBest;
        addresses_original += addressesOrg;
        addresses_best += addressesBest;
        seg_outliers += outliers;
        routes += 1;
        if (outliers === 0) {
            optimal_routes += 1;
        }

        if (unit === "m") {
            L_original_m += L_original;
            L_opt_m += L_opt;
        }

        if (unit === "sec") {
            L_original_sec += L_original;
            L_opt_sec += L_opt;
        }
    }

    return {
        DG_original,
        DG_best,
        seg_outliers,
        optimal_routes,
        routes,
        L_original_m,
        L_opt_m,
        L_original_sec,
        L_opt_sec,
        expense_original,
        expense_best,
        revenue_original,
        revenue_best,
        addresses_original,
        addresses_best
    };
}
