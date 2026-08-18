import { fmt } from "../utils/fmt.js";
import { appendHtml } from "../utils/dom.js";

export function renderIndexKPITables(container, type1, type2) {
    appendHtml(container, buildTable(
        "Type 1 Model (Fixed route)",
        type1
    ));
    appendHtml(container, buildTable(
        "Type 2 Model (Optimized route)",
        type2
    ));
}

function buildTable(title, k) {
    return `
        <div class="outlier-card kpi-box route-kpi-card">
            <h3 class="section-title">${title}</h3>
            <table class="kpi-table route-kpi-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="kpi-row-primary">
                        <td>Contribution margin original</td>
                        <td>${fmt(k.DG_original, "kr", 2)}</td>
                    </tr>
                    <tr class="kpi-row-primary">
                        <td>Contribution margin optimized</td>
                        <td>${fmt(k.DG_best, "kr", 2)}</td>
                    </tr>
                    <tr class="kpi-row-secondary kpi-row-section-start">
                        <td>Significant outliers</td>
                        <td>${k.seg_outliers}</td>
                    </tr>
                    <tr>
                        <td>Routes without significant outliers</td>
                        <td>${k.optimal_routes}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}
