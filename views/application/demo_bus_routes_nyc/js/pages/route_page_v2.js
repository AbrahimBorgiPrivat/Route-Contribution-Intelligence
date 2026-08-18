/**
 * Controller for route.html (v2).
 * Scenario-aware version of the route page.
 */

import { getQueryParam } from "../utils/url.js";
import { loadRegistry } from "../data/load_registry.js";
import { loadRouteJson } from "../data/load_route_json.js";
import { loadScenarioMetadata } from "../data/load_scenario_metadata.js";

import { renderKPITables } from "../ui/kpi_renderer.js";
import { renderOutlierTables } from "../ui/outlier_renderer.js";
import { renderRouteTables } from "../ui/route_tables.js";
import { initializeScenarioInfoModal } from "../ui/scenario_info_modal.js";
import { renderRouteMap } from "../map/map_render_route.js";

(async function () {
    const label = getQueryParam("label");
    const routeId = getQueryParam("route_id");
    const apr = getQueryParam("apr");
    const week = getQueryParam("week");

    if (!label || !routeId || !apr || !week) {
        console.error("Missing route parameters");
        return;
    }

    document.getElementById("route-title").textContent = `Route ${routeId}`;
    document.getElementById("route-meta").innerHTML = `
        <strong>Label:</strong> ${label} |
        <strong>Profile:</strong> ${apr} |
        <strong>Analysis period:</strong> ${week} |
        <strong>Route no.:</strong> ${routeId}
    `;

    const [registry, metadata] = await Promise.all([
        loadRegistry(),
        loadScenarioMetadata()
    ]);

    initializeScenarioInfoModal({
        metadata,
        label,
        apr,
        week
    });

    const norm = v => v?.toString().trim().toLowerCase();
    const entry = registry.find(r =>
        norm(r.label) === norm(label) &&
        norm(r.route_id) === norm(routeId) &&
        norm(r.APR_profile) === norm(apr) &&
        norm(r.Week_Profile) === norm(week)
    );
    if (!entry) {
        console.error("Route not found in registry");
        return;
    }

    const route = await loadRouteJson(entry.route_json);

    const leftColumn = document.getElementById("left-column");
    leftColumn.innerHTML = "";
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

    const basePath = `../data/${entry.route_json.replace(`/${routeId}.json`, "")}`;

    await renderRouteMap("route-map", {
        routeGeoURL: `${basePath}/${routeId}_route.geojson`,
        markerGeoURL: `${basePath}/${routeId}_markers.geojson`
    });

    const backLink = document.getElementById("back-link");
    if (backLink) {
        backLink.href =
            `overview.html?label=${encodeURIComponent(label)}`
            + `&apr=${encodeURIComponent(apr)}`
            + `&week=${encodeURIComponent(week)}`;
    }

    document.addEventListener("click", function (e) {
        const header = e.target.closest(".collapsible-header");
        if (!header) return;

        const targetId = header.dataset.target;
        const content = document.getElementById(targetId);
        if (!content) return;

        content.classList.toggle("hidden");
        header.classList.toggle("collapsed");
    });
})();
