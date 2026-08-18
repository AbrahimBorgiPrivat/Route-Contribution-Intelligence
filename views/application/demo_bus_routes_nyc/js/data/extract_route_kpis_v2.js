export function extractRouteKPIsV2(routeJson) {

    const result = { route_id: routeJson.route_id };

    const t1 = routeJson.solutions?.find(s => s.strict_order === true);
    const t2 = routeJson.solutions?.find(s => s.strict_order === false);

    function extract(solution, prefix) {
        const stopsOriginal = Array.isArray(solution?.stops_original)
            ? solution.stops_original
            : [];
        const stopsOptimal = Array.isArray(solution?.stops_optimal)
            ? solution.stops_optimal
            : [];

        const revenueOriginal = sumBy(stopsOriginal, "revenue");
        const revenueOptimal = sumBy(stopsOptimal, "revenue");
        const expenseOriginal = sumBy(stopsOriginal, "apr_cost");
        const expenseOptimal = sumBy(stopsOptimal, "apr_cost");
        const addressesOriginal = stopsOriginal.length;
        const addressesOptimal = stopsOptimal.length;

        result[`${prefix}_DG_original`] = solution?.DG_original ?? 0;
        result[`${prefix}_DG_best`] = solution?.DG_best ?? 0;
        result[`${prefix}_APR`] = solution?.APR ?? solution?.profile?.APR ?? 0;
        result[`${prefix}_revenue_original`] = revenueOriginal;
        result[`${prefix}_revenue_best`] = revenueOptimal;
        result[`${prefix}_expense_original`] = expenseOriginal;
        result[`${prefix}_expense_best`] = expenseOptimal;
        result[`${prefix}_addresses_original`] = addressesOriginal;
        result[`${prefix}_addresses_best`] = addressesOptimal;

        result[`${prefix}_seg_outliers`] =
            Array.isArray(solution?.S_outlier)
                ? solution.S_outlier.length
                : 0;

        result[`${prefix}_L_original`] = solution?.L_original ?? 0;
        result[`${prefix}_L_opt`] = solution?.L_opt ?? 0;

        result[`${prefix}_unit`] = solution?.profile?.unit ?? null;
    }

    extract(t1, "t1");
    extract(t2, "t2");

    return result;
}

function sumBy(rows, key) {
    return rows.reduce((sum, row) => sum + (Number(row?.[key]) || 0), 0);
}
