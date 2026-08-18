/**
 * Render KPI tables for Type 1 and Type 2 solutions.
 */
import { fmt } from "../utils/fmt.js";
import { appendHtml } from "../utils/dom.js";

export function renderKpiCard(container, title, kpis) {
    const revenueDelta = (Number(kpis.revenue_best) || 0) - (Number(kpis.revenue_original) || 0);
    const significantOutliers = Number(kpis.seg_outliers) || 0;

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
                        <td>Revenue original</td>
                        <td>${fmt(kpis.revenue_original, "kr", 2)}</td>
                    </tr>
                    <tr class="kpi-row-primary">
                        <td>Revenue optimized</td>
                        <td>${fmt(kpis.revenue_best, "kr", 2)}</td>
                    </tr>
                    <tr>
                        <td>Delta Revenue</td>
                        <td>${fmt(revenueDelta, "kr", 2)}</td>
                    </tr>
                    <tr class="kpi-row-section-start">
                        <td>Length original</td>
                        <td>${formatPrimaryLength(kpis, "original")}</td>
                    </tr>
                    <tr>
                        <td>Length optimized</td>
                        <td>${formatPrimaryLength(kpis, "optimized")}</td>
                    </tr>
                    <tr class="kpi-row-secondary kpi-row-section-start">
                        <td>Significant outliers</td>
                        <td>${fmt(significantOutliers)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `);
}

function formatPrimaryLength(kpis, variant) {
    const secKey = variant === "original" ? "L_original_sec" : "L_opt_sec";
    const meterKey = variant === "original" ? "L_original_m" : "L_opt_m";

    if ((Number(kpis[secKey]) || 0) > 0) {
        return fmt(kpis[secKey], "sec", 0, "min");
    }

    if ((Number(kpis[meterKey]) || 0) > 0) {
        return fmt(kpis[meterKey], "m", 0);
    }

    return "-";
}
