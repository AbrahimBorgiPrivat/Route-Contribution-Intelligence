import { fetchRoute } from "../data/fetch_route.js";
import { extractRouteKPIs } from "../data/route_kpis.js";

export async function buildIndexTable(routes, kpis) {
    const thead = document.getElementById("table-head");
    const tbody = document.getElementById("table-body");

    let headHtml = "<tr>";
    kpis.forEach(k => headHtml += `<th>${k.name}</th>`);
    headHtml += "<th>Open route</th></tr>";
    thead.innerHTML = headHtml;

    tbody.innerHTML = "";

    for (const r of routes) {
        const routeData = await fetchRoute(r.route_id);
        const kpiRow = extractRouteKPIs(routeData);

        let rowHtml = "<tr>";
        kpis.forEach(k => {
            let v = kpiRow[k.key];
            if (typeof v === "number") {
                v = Math.round(v);
            }
            rowHtml += `<td>${v}</td>`;
        });

        rowHtml += `
            <td class="route-action-cell">
                <a class="cta-link" href="route.html?route_id=${kpiRow.route_id}">
                    <span>Open route</span>
                    <span class="cta-link-icon">→</span>
                </a>
            </td>
        </tr>`;

        tbody.insertAdjacentHTML("beforeend", rowHtml);
    }

    $(document).ready(() => {
        $("#route-table").DataTable({
            pageLength: 10,
            lengthChange: true,
            info: false
        });
        $("input[type=search]").attr("id", "route-search");
    });
}
