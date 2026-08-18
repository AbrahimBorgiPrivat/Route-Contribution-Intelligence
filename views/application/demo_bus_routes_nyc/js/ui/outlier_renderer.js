/**
 * Render outlier tables (Type 1 + Type 2)
 * with collapsible behavior and DataTables integration.
 */

import { appendHtml } from "../utils/dom.js";
import { fmt, fmtKr } from "../utils/fmt.js";

export function renderOutlierTables(container, solutions) {
    solutions.forEach(s => {
        const title = s.strict_order
            ? "Type 1 Model (Fixed route)"
            : "Type 2 Model (Optimized route)";
        const tableId = `outlier-${title.replace(/\s+/g, "")}`;

        appendHtml(container, `
            <div class="outlier-card route-outlier-card outlier-block">
                <div class="collapsible-header route-card-header" data-target="${tableId}">
                    <div>
                        <div class="route-card-eyebrow">Outlier overview</div>
                        <h3 class="section-title">${title}</h3>
                    </div>
                    <span class="route-card-toggle">Show table</span>
                </div>

                <div id="${tableId}" class="collapsible-content hidden">
                    <div class="route-card-table-wrap">
                        <table class="display outlier-table route-summary-table">
                            <thead>
                                <tr>
                                    <th>Outlier</th>
                                    <th>Increase</th>
                                    <th>Length</th>
                                    <th>Gain</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.entries(s.coverage_change).map(([S, val]) => {
                                    const dist = s.distance_change[S] ?? 0;
                                    return `
                                        <tr>
                                            <td>${S}</td>
                                            <td data-order="${Number(val) || 0}" data-sort="${Number(val) || 0}">${fmtKr(val, 2)}</td>
                                            <td data-order="${Number(dist) || 0}" data-sort="${Number(dist) || 0}">${fmt(dist, s.profile.unit, 0, "min")}</td>
                                            <td data-order="${Number(dist * s.APR) || 0}" data-sort="${Number(dist * s.APR) || 0}">${fmtKr(dist * s.APR, 0)}</td>
                                        </tr>
                                    `;
                                }).join("")}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `);
    });

    $(".outlier-table").DataTable({
        pageLength: 10,
        lengthChange: true,
        searching: true,
        info: false,
        ordering: true,
        pagingType: "simple"
    });
}
