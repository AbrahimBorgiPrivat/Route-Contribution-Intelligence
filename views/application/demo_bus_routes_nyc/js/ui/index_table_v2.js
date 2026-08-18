import { extractRouteKPIsV2 } from "../data/extract_route_kpis_v2.js";
import { fmt } from "../utils/fmt.js";
import { formatTransportform } from "../utils/transportform.js";

export function buildIndexTableV2(routeJsons, context) {
    const { label, apr, week, onFilterChange = () => {} } = context;
    const thead = document.getElementById("table-head");
    const tbody = document.getElementById("table-body");
    const rows = [];

    thead.innerHTML = `
        <tr>
            <th rowspan="2">Route</th>
            <th rowspan="2">Transport mode</th>
            <th colspan="6" class="route-table-group-header t1-group-header">Type 1 (Fixed route)</th>
            <th colspan="6" class="route-table-group-header t2-group-header">Type 2 (Optimized route)</th>
            <th rowspan="2">Next step</th>
        </tr>
        <tr>
            <th class="route-table-subhead t1-subhead">Length (Orig)</th>
            <th class="route-table-subhead t1-subhead">Length (Opt)</th>
            <th class="route-table-subhead t1-subhead">CM (Orig)</th>
            <th class="route-table-subhead t1-subhead">CM (Opt)</th>
            <th class="route-table-subhead t1-subhead delta-subhead">Delta CM</th>
            <th class="route-table-subhead t1-subhead">Sign. outliers</th>
            <th class="route-table-subhead t2-subhead">Length (Orig)</th>
            <th class="route-table-subhead t2-subhead">Length (Opt)</th>
            <th class="route-table-subhead t2-subhead">CM (Orig)</th>
            <th class="route-table-subhead t2-subhead">CM (Opt)</th>
            <th class="route-table-subhead t2-subhead delta-subhead">Delta CM</th>
            <th class="route-table-subhead t2-subhead">Sign. outliers</th>
        </tr>
    `;

    tbody.innerHTML = "";

    for (const routeJson of routeJsons) {
        const k = extractRouteKPIsV2(routeJson);
        const transportform = formatTransportform(routeJson.solutions?.[0]?.profile?.profile);
        const routeUrl =
            `route.html?label=${encodeURIComponent(label)}`
            + `&route_id=${encodeURIComponent(k.route_id)}`
            + `&apr=${encodeURIComponent(apr)}`
            + `&week=${encodeURIComponent(week)}`;

        const t1Delta = Number(k.t1_DG_best - k.t1_DG_original) || 0;
        const t2Delta = Number(k.t2_DG_best - k.t2_DG_original) || 0;

        rows.push({
            routeId: String(k.route_id),
            transportform
        });

        tbody.insertAdjacentHTML("beforeend", `
            <tr>
                <td data-order="${Number(k.route_id) || 0}" class="route-id-cell">${k.route_id}</td>
                <td class="transportform-cell">${transportform}</td>
                <td data-order="${Number(k.t1_L_original) || 0}" class="scenario-cell t1-cell">${fmt(k.t1_L_original, k.t1_unit, 0, "min")}</td>
                <td data-order="${Number(k.t1_L_opt) || 0}" class="scenario-cell t1-cell">${fmt(k.t1_L_opt, k.t1_unit, 0, "min")}</td>
                <td data-order="${Number(k.t1_DG_original) || 0}" class="scenario-cell t1-cell">${fmt(k.t1_DG_original, "kr", 2)}</td>
                <td data-order="${Number(k.t1_DG_best) || 0}" class="scenario-cell t1-cell">${fmt(k.t1_DG_best, "kr", 2)}</td>
                <td data-order="${t1Delta}" class="scenario-cell t1-cell delta-cell">${renderDeltaPill(t1Delta)}</td>
                <td data-order="${Number(k.t1_seg_outliers) || 0}" class="scenario-cell t1-cell outlier-cell">${k.t1_seg_outliers}</td>
                <td data-order="${Number(k.t2_L_original) || 0}" class="scenario-cell t2-cell">${fmt(k.t2_L_original, k.t2_unit, 0, "min")}</td>
                <td data-order="${Number(k.t2_L_opt) || 0}" class="scenario-cell t2-cell">${fmt(k.t2_L_opt, k.t2_unit, 0, "min")}</td>
                <td data-order="${Number(k.t2_DG_original) || 0}" class="scenario-cell t2-cell">${fmt(k.t2_DG_original, "kr", 2)}</td>
                <td data-order="${Number(k.t2_DG_best) || 0}" class="scenario-cell t2-cell">${fmt(k.t2_DG_best, "kr", 2)}</td>
                <td data-order="${t2Delta}" class="scenario-cell t2-cell delta-cell">${renderDeltaPill(t2Delta)}</td>
                <td data-order="${Number(k.t2_seg_outliers) || 0}" class="scenario-cell t2-cell outlier-cell">${k.t2_seg_outliers}</td>
                <td class="route-action-cell">
                    <a class="open-link cta-link" href="${routeUrl}" title="Open route">
                        <span>Open route</span>
                        <span class="cta-link-icon">></span>
                    </a>
                </td>
            </tr>
        `);
    }

    const table = $("#route-table").DataTable({
        pageLength: 10,
        lengthChange: true,
        info: false,
        autoWidth: false
    });

    const adjustLayout = () => table.columns.adjust();
    window.addEventListener("resize", adjustLayout);
    setTimeout(adjustLayout, 0);

    buildTableFilters(table, rows, onFilterChange);
}

function renderDeltaPill(value) {
    const numericValue = Number(value) || 0;
    const state =
        numericValue > 0
            ? "positive"
            : numericValue < 0
                ? "negative"
                : "neutral";

    return `
        <span class="delta-pill ${state}">
            ${fmt(numericValue, "kr", 2)}
        </span>
    `;
}

function buildTableFilters(table, rows, onFilterChange) {
    const container = document.getElementById("route-table-filters");
    if (!container) return;

    container.innerHTML = "";

    const selectedTransportforms = new Set();
    const selectedRoutes = new Set();

    const transportforms = [...new Set(rows.map(r => r.transportform))].sort();
    const routes = [...new Set(rows.map(r => r.routeId))].sort((a, b) =>
        a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
    );

    const filterFn = function (_settings, data) {
        const route = String(data[0] ?? "");
        const transportform = String(data[1] ?? "");

        const transportOk =
            selectedTransportforms.size === 0 || selectedTransportforms.has(transportform);

        const routeOk =
            selectedRoutes.size === 0 || selectedRoutes.has(route);

        return transportOk && routeOk;
    };

    $.fn.dataTable.ext.search.push(filterFn);

    const redraw = () => {
        table.draw();
        onFilterChange({
            transportforms: [...selectedTransportforms],
            routes: [...selectedRoutes]
        });
    };

    container.appendChild(createMultiSelectFilter({
        title: "Transport mode",
        options: transportforms,
        selected: selectedTransportforms,
        onChange: redraw,
        searchPlaceholder: "Search transport mode"
    }));

    container.appendChild(createMultiSelectFilter({
        title: "Route",
        options: routes,
        selected: selectedRoutes,
        onChange: redraw,
        searchPlaceholder: "Search route"
    }));

    redraw();
}

function createMultiSelectFilter({
    title,
    options,
    selected,
    onChange,
    searchPlaceholder
}) {
    const wrapper = document.createElement("div");
    wrapper.className = "table-filter";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "table-filter-trigger";

    const triggerText = document.createElement("span");
    triggerText.innerHTML = `
        <span class="table-filter-label">${title}</span>
        <span class="table-filter-summary">All</span>
    `;

    const chevron = document.createElement("span");
    chevron.className = "table-filter-chevron";
    chevron.textContent = "v";

    trigger.appendChild(triggerText);
    trigger.appendChild(chevron);

    const panel = document.createElement("div");
    panel.className = "table-filter-panel hidden";

    const search = document.createElement("input");
    search.type = "search";
    search.className = "table-filter-search";
    search.placeholder = searchPlaceholder;

    const actions = document.createElement("div");
    actions.className = "table-filter-actions";

    const selectAllBtn = document.createElement("button");
    selectAllBtn.type = "button";
    selectAllBtn.className = "table-filter-action";
    selectAllBtn.textContent = "Select all";

    const clearBtn = document.createElement("button");
    clearBtn.type = "button";
    clearBtn.className = "table-filter-action";
    clearBtn.textContent = "Clear";

    actions.appendChild(selectAllBtn);
    actions.appendChild(clearBtn);

    const optionList = document.createElement("div");
    optionList.className = "table-filter-options";

    const optionItems = options.map(option => {
        const label = document.createElement("label");
        label.className = "table-filter-option";
        label.dataset.value = option.toLowerCase();

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = option;

        const text = document.createElement("span");
        text.textContent = option;

        checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
                selected.add(option);
            } else {
                selected.delete(option);
            }
            updateSummary();
            onChange();
        });

        label.appendChild(checkbox);
        label.appendChild(text);
        optionList.appendChild(label);
        return { label, checkbox, option };
    });

    const empty = document.createElement("div");
    empty.className = "table-filter-empty hidden";
    empty.textContent = "No results";
    optionList.appendChild(empty);

    const updateSummary = () => {
        const summary = triggerText.querySelector(".table-filter-summary");
        if (selected.size === 0) {
            summary.textContent = "All";
            return;
        }
        if (selected.size <= 2) {
            summary.textContent = [...selected].join(", ");
            return;
        }
        summary.textContent = `${selected.size} selected`;
    };

    const filterOptions = () => {
        const term = search.value.trim().toLowerCase();
        let visibleCount = 0;

        optionItems.forEach(({ label }) => {
            const isVisible = !term || label.dataset.value.includes(term);
            label.classList.toggle("hidden", !isVisible);
            if (isVisible) visibleCount += 1;
        });

        empty.classList.toggle("hidden", visibleCount !== 0);
    };

    selectAllBtn.addEventListener("click", () => {
        optionItems.forEach(({ checkbox, option }) => {
            checkbox.checked = true;
            selected.add(option);
        });
        updateSummary();
        onChange();
    });

    clearBtn.addEventListener("click", () => {
        optionItems.forEach(({ checkbox, option }) => {
            checkbox.checked = false;
            selected.delete(option);
        });
        updateSummary();
        onChange();
    });

    search.addEventListener("input", filterOptions);

    trigger.addEventListener("click", () => {
        const isHidden = panel.classList.contains("hidden");
        document.querySelectorAll(".table-filter-panel").forEach(el => el.classList.add("hidden"));
        if (isHidden) {
            panel.classList.remove("hidden");
            search.focus();
        }
    });

    document.addEventListener("click", e => {
        if (!wrapper.contains(e.target)) {
            panel.classList.add("hidden");
        }
    });

    panel.appendChild(search);
    panel.appendChild(actions);
    panel.appendChild(optionList);

    wrapper.appendChild(trigger);
    wrapper.appendChild(panel);

    updateSummary();
    return wrapper;
}
