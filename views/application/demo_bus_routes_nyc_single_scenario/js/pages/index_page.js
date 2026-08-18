import { fetchRoutesIndex } from "../data/fetch_routes_index.js";
import { fetchRoute } from "../data/fetch_route.js";
import { extractRouteKPIs } from "../data/route_kpis.js";
import { aggregateKPIs } from "../data/index_kpi_aggregate.js";
import { renderIndexKPITables } from "../ui/index_kpi_tables.js";
import { buildIndexTable } from "../ui/index_table.js";
import { renderIndexMap } from "../map/map_render_index.js";

(async function () {
    const index = await fetchRoutesIndex();
    const routeKPIs = [];
    for (const r of index.routes) {
        const routeData = await fetchRoute(r.route_id);
        routeKPIs.push(extractRouteKPIs(routeData));
    }
    const type1KPIs = aggregateKPIs(routeKPIs, true);
    const type2KPIs = aggregateKPIs(routeKPIs, false);
    const kpiContainer = document.getElementById("index-kpi-tables");
    renderIndexKPITables(kpiContainer, type1KPIs, type2KPIs);
    await buildIndexTable(index.routes, index.kpis);
    await renderIndexMap("map", index.routes);
})();
