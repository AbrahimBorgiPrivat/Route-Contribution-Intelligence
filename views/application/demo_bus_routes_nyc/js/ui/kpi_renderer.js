/**
 * Render KPI tables for Type 1 and Type 2 solutions.
 */
import { fmt } from "../utils/fmt.js";
import { appendHtml } from "../utils/dom.js";

export function renderKPITables(container, solutions) {
    solutions.forEach(s => {
        const title = s.strict_order
            ? "Type 1 Model (Fixed route)"
            : "Type 2 Model (Optimized route)";

        appendHtml(container, `
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
                            <td>${fmt(s.DG_original, "kr", 2)}</td>
                        </tr>
                        <tr class="kpi-row-primary">
                            <td>Contribution margin optimized</td>
                            <td>${fmt(s.DG_best, "kr", 2)}</td>
                        </tr>
                        <tr>
                            <td>Δ Contribution margin</td>
                            <td>${fmt(s.C2_max, "kr", 2)}</td>
                        </tr>
                        <tr class="kpi-row-section-start">
                            <td>Length original</td>
                            <td>${fmt(s.L_original, s?.profile?.unit ?? "", 0, "min")}</td>
                        </tr>
                        <tr>
                            <td>Length optimized</td>
                            <td>${fmt(s.L_opt, s?.profile?.unit ?? "", 0, "min")}</td>
                        </tr>
                        <tr class="kpi-row-secondary kpi-row-section-start">
                            <td>Significant outliers</td>
                            <td>${(s.S_outlier || []).length}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `);
    });
}
