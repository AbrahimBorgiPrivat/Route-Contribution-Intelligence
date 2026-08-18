import { getQueryParam } from "../utils/url.js";
import { fetchRoute } from "../data/fetch_route.js";
import { renderKPITables } from "../ui/kpi_renderer.js";
import { renderOutlierTables } from "../ui/outlier_renderer.js";
import { renderRouteTables } from "../ui/route_tables.js";
import { renderRouteMap } from "../map/map_render_route.js";

(async function () {
    const routeId = getQueryParam("route_id");
    document.getElementById("route-title").textContent = `Route ${routeId}`;

    const routeMeta = document.getElementById("route-meta");
    if (routeMeta) {
        routeMeta.innerHTML = `
            <strong>Label:</strong> All Routes |
            <strong>Profile:</strong> MTA Car New York |
            <strong>Analysis period:</strong> MTA 2024-10-15 |
            <strong>Route no.:</strong> ${routeId}
        `;
    }

    const route = await fetchRoute(routeId);

    const leftColumn = document.getElementById("left-column");
    const kpiContainer = document.createElement("div");
    kpiContainer.className = "kpi-grid";
    leftColumn.appendChild(kpiContainer);

    renderKPITables(kpiContainer, route.solutions);
    renderOutlierTables(leftColumn, route.solutions);

    const t1Solution = route.solutions.find(s => s.strict_order === true);
    const t2Solution = route.solutions.find(s => s.strict_order === false);
    const t1TablesContainer = document.getElementById("t1-tables");
    const t2TablesContainer = document.getElementById("t2-tables");

    if (t1Solution && t1TablesContainer) {
        renderRouteTables(t1TablesContainer, t1Solution);
    }

    if (t2Solution && t2TablesContainer) {
        renderRouteTables(t2TablesContainer, t2Solution);
    }

    const base = `../data/routes/${routeId}`;
    const routeGeoURL = `${base}/${route.geojson_route}`;
    const markerGeoURL = `${base}/${route.geojson_markers}`;

    await renderRouteMap("route-map", {
        routeGeoURL,
        markerGeoURL
    });

    document.addEventListener("click", function (e) {
        const header = e.target.closest(".collapsible-header");
        if (!header) return;

        const targetId = header.dataset.target;
        if (!targetId) return;

        const content = document.getElementById(targetId);
        if (!content) return;

        content.classList.toggle("hidden");
        header.classList.toggle("collapsed");
    });
})();
