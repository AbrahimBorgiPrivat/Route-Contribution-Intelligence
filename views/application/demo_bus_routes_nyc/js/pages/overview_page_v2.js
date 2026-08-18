import { getQueryParam } from "../utils/url.js";
import { fetchScenarioRoutes } from "../data/fetch_scenario_routes.js";
import { extractRouteKPIsV2 } from "../data/extract_route_kpis_v2.js";
import { aggregateKPIs } from "../data/aggregate_kpis.js";

import { renderKpiCard } from "../ui/kpi_cards.js";
import { renderKpiChangeCards } from "../ui/kpi_change_cards.js";
import { buildIndexTableV2 } from "../ui/index_table_v2.js";
import { initializeScenarioInfoModal } from "../ui/scenario_info_modal.js";
import { formatTransportform } from "../utils/transportform.js";
import { renderIndexMap } from "../map/map_render_index_v2.js";

(async function () {
    const label = getQueryParam("label");
    const apr = getQueryParam("apr");
    const week = getQueryParam("week");
    if (!label || !apr || !week) {
        console.error("Missing URL parameters");
        return;
    }

    document.getElementById("scenario-title").textContent = `${label} - ${apr}`;
    document.getElementById("scenario-meta").innerHTML = `
        <div class="scenario-meta-content">
            <strong>Label:</strong> ${label}
            <span class="meta-separator">|</span>
            <strong>Profile:</strong> ${apr}
            <span class="meta-separator">|</span>
            <strong>Analysis period:</strong> ${week}
        </div>
    `;

    const kpiContainer = document.getElementById("index-kpi-tables");
    const routeFilterContainer = document.getElementById("route-table-filters");
    const tableHead = document.getElementById("table-head");
    const tableBody = document.getElementById("table-body");

    kpiContainer.innerHTML = `<div class="async-feedback">Calculating scenario...</div>`;
    routeFilterContainer.innerHTML = `<div class="async-feedback">Calculating route overview...</div>`;
    tableHead.innerHTML = "";
    tableBody.innerHTML = "";

    const { routes, routeJsons, metadata } = await fetchScenarioRoutes(label, apr, week);
    initializeScenarioInfoModal({
        metadata,
        label,
        apr,
        week
    });
    if (!routeJsons.length) {
        console.warn("No routes found for this scenario");
        return;
    }

    const routesWithMeta = routes.map((route, index) => ({
        ...route,
        transportform: formatTransportform(
            routeJsons[index]?.solutions?.[0]?.profile?.profile
        )
    }));
    const routeKPIs = routeJsons.map(extractRouteKPIsV2);
    const type1 = aggregateKPIs(routeKPIs, true);
    const type2 = aggregateKPIs(routeKPIs, false);
    kpiContainer.innerHTML = "";

    const changeGrid = document.createElement("div");
    changeGrid.className = "kpi-change-grid";
    kpiContainer.appendChild(changeGrid);
    renderKpiChangeCards(changeGrid, [
        {
            title: "Type 1 (Original) -> Type 1 (Optimized)",
            from: {
                revenue: type1.revenue_original,
                expense: type1.expense_original,
                DG: type1.DG_original,
                lengthMeters: type1.L_original_m,
                lengthSeconds: type1.L_original_sec
            },
            to: {
                revenue: type1.revenue_best,
                expense: type1.expense_best,
                DG: type1.DG_best,
                lengthMeters: type1.L_opt_m,
                lengthSeconds: type1.L_opt_sec
            }
        },
        {
            title: "Type 1 (Original) -> Type 2 (Original)",
            from: {
                revenue: type1.revenue_original,
                expense: type1.expense_original,
                DG: type1.DG_original,
                lengthMeters: type1.L_original_m,
                lengthSeconds: type1.L_original_sec
            },
            to: {
                revenue: type2.revenue_original,
                expense: type2.expense_original,
                DG: type2.DG_original,
                lengthMeters: type2.L_original_m,
                lengthSeconds: type2.L_original_sec
            }
        },
        {
            title: "Type 2 (Original) -> Type 2 (Optimized)",
            from: {
                revenue: type2.revenue_original,
                expense: type2.expense_original,
                DG: type2.DG_original,
                lengthMeters: type2.L_original_m,
                lengthSeconds: type2.L_original_sec
            },
            to: {
                revenue: type2.revenue_best,
                expense: type2.expense_best,
                DG: type2.DG_best,
                lengthMeters: type2.L_opt_m,
                lengthSeconds: type2.L_opt_sec
            }
        },
        {
            title: "Type 1 (Original) -> Type 2 (Optimized)",
            from: {
                revenue: type1.revenue_original,
                expense: type1.expense_original,
                DG: type1.DG_original,
                lengthMeters: type1.L_original_m,
                lengthSeconds: type1.L_original_sec
            },
            to: {
                revenue: type2.revenue_best,
                expense: type2.expense_best,
                DG: type2.DG_best,
                lengthMeters: type2.L_opt_m,
                lengthSeconds: type2.L_opt_sec
            }
        }
    ]);

    const grid = document.createElement("div");
    grid.className = "kpi-grid";
    kpiContainer.appendChild(grid);
    renderKpiCard(grid, "Type 1 (Fixed route)", type1);
    renderKpiCard(grid, "Type 2 (Optimized route)", type2);

    const mapController = await renderIndexMap("map", routesWithMeta);
    buildIndexTableV2(routeJsons, {
        label,
        apr,
        week,
        onFilterChange: filters => mapController.applyFilters(filters)
    });
})();
