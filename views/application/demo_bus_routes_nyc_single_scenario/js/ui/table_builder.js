/**
 * Build a simple table structure for the index page.
 */
export function buildIndexTable(containerHead, containerBody, routes, kpis) {

    let head = "<tr>";
    kpis.forEach(k => head += `<th>${k.name}</th>`);
    head += "<th>Åben</th></tr>";
    containerHead.innerHTML = head;

    routes.forEach(r => {
        containerBody.insertAdjacentHTML("beforeend", `
            <tr>
                <td>${r.route_id}</td>
                <td>-</td>
                <td>-</td>
                <td>
                    <a class="btn-route" href="route.html?route_id=${r.route_id}">
                        Åben
                    </a>
                </td>
            </tr>
        `);
    });
}