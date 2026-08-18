/**
 * Render route stop tables for Original and Optimized routes.
 */

import { appendHtml } from "../utils/dom.js";
import { fmtKr, fmt } from "../utils/fmt.js";

export function renderRouteTables(container, solution) {
    if (!solution) {
        appendHtml(container, `<p>No stop data available.</p>`);
        return;
    }

    const isType1 = solution.strict_order === true;
    const titlePrefix = isType1 ? "Type 1" : "Type 2";
    container.innerHTML = "";

    if (Array.isArray(solution.stops_original) && solution.stops_original.length > 0) {
        renderTableSection(
            container,
            `${titlePrefix} - Original route`,
            solution.stops_original,
            `${titlePrefix}-original`,
            false,
            solution.profile.unit
        );
    }

    if (Array.isArray(solution.stops_optimal) && solution.stops_optimal.length > 0) {
        renderTableSection(
            container,
            `${titlePrefix} - Optimized route`,
            solution.stops_optimal,
            `${titlePrefix}-optimal`,
            true,
            solution.profile.unit
        );
    }
}

function renderTableSection(
    container,
    title,
    rows,
    tableIdSuffix,
    highlightOutliers,
    unitFormat
) {
    const tableId = `route-table-${tableIdSuffix.replace(/\s+/g, "")}`;
    const sectionId = `${tableId}-section`;
    const isOptimal = tableIdSuffix.includes("optimal");

    appendHtml(container, `
        <div class="outlier-card route-stop collapsible route-stop-card" id="${sectionId}">
            <div class="collapsible-header route-card-header route-stop-card-header">
                <div>
                    <h3 class="section-title">${title}</h3>
                </div>
                <span class="route-card-toggle">Show table</span>
            </div>
            <div class="collapsible-content">
                <table class="display route-stop-table" id="${tableId}">
                    <thead>
                        <tr>
                            <th>Route no.</th>
                            <th>Original no.</th>
                            <th>Address</th>
                            <th>Stops</th>
                            <th>Revenue</th>
                            <th>Length to next</th>
                            <th>APR x length</th>
                            ${!isOptimal ? "<th>Significant outlier</th>" : ""}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(r => `
                            <tr class="${highlightOutliers && r.is_significant_outlier ? "outlier-row" : ""}">
                                <td data-order="${Number(r.sequence_index) || 0}" data-sort="${Number(r.sequence_index) || 0}">${r.sequence_index}</td>
                                <td data-order="${Number(r.route_number) || 0}" data-sort="${Number(r.route_number) || 0}">${r.route_number}</td>
                                <td>${r.address ?? ""}</td>
                                <td data-order="${Number(r.postboxes) || 0}" data-sort="${Number(r.postboxes) || 0}">${r.postboxes}</td>
                                <td data-order="${Number(r.revenue) || 0}" data-sort="${Number(r.revenue) || 0}">${fmtKr(r.revenue, 2)}</td>
                                <td data-order="${Number(r.distance_to_next) || 0}" data-sort="${Number(r.distance_to_next) || 0}">${fmt(r.distance_to_next, unitFormat)}</td>
                                <td data-order="${Number(r.apr_cost) || 0}" data-sort="${Number(r.apr_cost) || 0}">${fmtKr(r.apr_cost, 0)}</td>
                                ${!isOptimal ? `<td data-order="${r.is_significant_outlier ? 1 : 0}" data-sort="${r.is_significant_outlier ? 1 : 0}">${r.is_significant_outlier ? "Yes" : ""}</td>` : ""}
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        </div>
    `);

    const dt = $(`#${tableId}`).DataTable({
        pageLength: 10,
        lengthChange: true,
        searching: true,
        info: false,
        ordering: true,
        pagingType: "simple",
        dom: "lfrtipB",
        buttons: ["csv"]
    });

    const section = document.getElementById(sectionId);
    const header = section.querySelector(".collapsible-header");
    const content = section.querySelector(".collapsible-content");

    content.style.display = "none";
    header.classList.add("collapsed");

    header.addEventListener("click", () => {
        const isOpen = content.style.display === "block";
        content.style.display = isOpen ? "none" : "block";
        header.classList.toggle("collapsed", isOpen);
        if (!isOpen) {
            setTimeout(() => dt.columns.adjust(), 50);
        }
    });
}
