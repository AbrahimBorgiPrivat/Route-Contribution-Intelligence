import { buildScenarioIndexRows } from "../data/build_scenario_index_rows.js";
import { fmtKr } from "../utils/fmt.js";

export function renderScenarioIndexSummary(container, {
    entries,
    aprOrder,
    weekOrder,
    compareLabels,
}) {
    container.innerHTML = "";

    const section = document.createElement("section");
    section.className = "index-summary-section";
    container.appendChild(section);

    const title = document.createElement("h2");
    title.className = "section-title index-summary-section__title";
    title.textContent = "Scenario overview";
    section.appendChild(title);

    if (!Array.isArray(entries) || entries.length === 0) {
        section.appendChild(createEmptyState());
        return;
    }

    const weeks = getOrderedValues(
        entries.map(entry => entry.Week_Profile),
        weekOrder
    );

    renderWeekSelector(section, {
        weeks,
        entries,
        aprOrder,
        compareLabels,
    });
}

function createEmptyState() {
    const empty = document.createElement("div");
    empty.className = "index-summary-empty";
    empty.textContent = "No scenarios match the selected filters.";
    return empty;
}

function renderWeekSelector(root, {
    weeks,
    entries,
    aprOrder,
    compareLabels,
}) {
    let selectedIndex = 0;
    let loadVersion = 0;

    const card = document.createElement("article");
    card.className = "index-summary-card";
    root.appendChild(card);

    const headerRow = document.createElement("div");
    headerRow.className = "week-header index-summary-week-header";

    const weekTitle = document.createElement("div");
    weekTitle.className = "week-title index-summary-week-title";

    const weekMeta = document.createElement("div");
    weekMeta.className = "index-summary-week-meta";
    headerRow.append(weekTitle, weekMeta);
    card.appendChild(headerRow);

    const navRow = document.createElement("div");
    navRow.className = "week-nav-row index-summary-nav-row";

    const btnPrev = document.createElement("button");
    btnPrev.type = "button";
    btnPrev.className = "week-arrow";
    btnPrev.textContent = "<";

    const btnNext = document.createElement("button");
    btnNext.type = "button";
    btnNext.className = "week-arrow";
    btnNext.textContent = ">";

    const tableHost = document.createElement("div");
    tableHost.className = "index-summary-table-host";

    navRow.append(btnPrev, tableHost, btnNext);
    card.appendChild(navRow);

    const pillRow = document.createElement("div");
    pillRow.className = "week-pill-row";
    card.appendChild(pillRow);

    weeks.forEach((week, index) => {
        const pill = document.createElement("button");
        pill.type = "button";
        pill.className = "week-pill";
        pill.textContent = week;
        pill.addEventListener("click", () => {
            void showWeek(index);
        });
        pillRow.appendChild(pill);
    });

    btnPrev.addEventListener("click", () => {
        void showWeek(selectedIndex - 1);
    });
    btnNext.addEventListener("click", () => {
        void showWeek(selectedIndex + 1);
    });

    async function showWeek(index) {
        selectedIndex = (index + weeks.length) % weeks.length;
        const activeWeek = weeks[selectedIndex];
        const weekEntries = entries.filter(entry => entry.Week_Profile === activeWeek);
        loadVersion += 1;
        const currentLoadVersion = loadVersion;

        pillRow.querySelectorAll(".week-pill").forEach((pill, pillIndex) => {
            pill.classList.toggle("active", pillIndex === selectedIndex);
        });

        weekTitle.textContent = `Analysis period: ${activeWeek}`;
        weekMeta.textContent = `${countScenarioEntries(weekEntries)} scenarios`;

        tableHost.innerHTML = "";
        tableHost.appendChild(createFeedbackState("Calculating scenario overview..."));

        try {
            const rows = await buildScenarioIndexRows(weekEntries);
            if (currentLoadVersion !== loadVersion) {
                return;
            }

            tableHost.innerHTML = "";
            tableHost.appendChild(createWeekTable(rows, activeWeek, aprOrder, compareLabels));
        } catch (_) {
            if (currentLoadVersion !== loadVersion) {
                return;
            }

            tableHost.innerHTML = "";
            tableHost.appendChild(createFeedbackState("The scenario overview could not be calculated."));
        }
    }

    void showWeek(0);
}

function createWeekTable(rows, activeWeek, aprOrder, compareLabels) {
    const tableWrap = document.createElement("div");
    tableWrap.className = "index-summary-table-wrap";

    const table = document.createElement("table");
    table.className = "index-summary-table";

    table.appendChild(createHead());
    table.appendChild(createBody(rows, activeWeek, aprOrder, compareLabels));
    tableWrap.appendChild(table);

    return tableWrap;
}

function createHead() {
    const thead = document.createElement("thead");

    const groupRow = document.createElement("tr");
    groupRow.innerHTML = `
        <th rowspan="2">Profile</th>
        <th rowspan="2">Label</th>
        <th colspan="7" class="route-table-group-header t1-group-header">Type 1 (Fixed route)</th>
        <th colspan="7" class="route-table-group-header t2-group-header">Type 2 (Optimized route)</th>
        <th rowspan="2">Next step</th>
    `;

    const subRow = document.createElement("tr");
    [
        ["t1-subhead", "CM (Orig)"],
        ["t1-subhead", "CM (Opt)"],
        ["t1-subhead", "Revenue (Orig)"],
        ["t1-subhead", "Revenue (Opt)"],
        ["t1-subhead", "Costs (Orig)"],
        ["t1-subhead", "Costs (Opt)"],
        ["t1-subhead", "Sign. outliers"],
        ["t2-subhead", "CM (Orig)"],
        ["t2-subhead", "CM (Opt)"],
        ["t2-subhead", "Revenue (Orig)"],
        ["t2-subhead", "Revenue (Opt)"],
        ["t2-subhead", "Costs (Orig)"],
        ["t2-subhead", "Costs (Opt)"],
        ["t2-subhead", "Sign. outliers"],
    ].forEach(([className, text]) => {
        const th = document.createElement("th");
        th.className = `route-table-subhead ${className}`;
        th.textContent = text;
        subRow.appendChild(th);
    });

    thead.append(groupRow, subRow);
    return thead;
}

function createBody(rows, activeWeek, aprOrder, compareLabels) {
    const tbody = document.createElement("tbody");
    const groupedRows = groupRows(rows, aprOrder, compareLabels);

    groupedRows.forEach(aprGroup => {
        const aprSpan = aprGroup.rows.length;
        let aprRendered = false;

        aprGroup.rows.forEach(summaryRow => {
            const tr = document.createElement("tr");

            if (!aprRendered) {
                tr.appendChild(createMergedCell(
                    aprGroup.apr,
                    aprSpan,
                    "index-summary-table__merge index-summary-table__apr"
                ));
                aprRendered = true;
            }

            tr.appendChild(createTextCell(
                summaryRow.label,
                "index-summary-table__merge index-summary-table__label"
            ));

            appendTypeCells(tr, summaryRow.t1, "t1");
            appendTypeCells(tr, summaryRow.t2, "t2");
            tr.appendChild(createScenarioActionCell(summaryRow, activeWeek));
            tbody.appendChild(tr);
        });
    });

    return tbody;
}

function groupRows(rows, aprOrder, compareLabels) {
    const aprs = getOrderedValues(rows.map(row => row.apr_profile), aprOrder);

    return aprs.map(apr => {
        const aprRows = rows.filter(row => row.apr_profile === apr);
        const labels = [...new Set(aprRows.map(row => row.label))].sort(compareLabels);

        return {
            apr,
            rows: labels.map(label => aprRows.find(row => row.label === label)).filter(Boolean)
        };
    });
}

function appendTypeCells(tr, typeRow, typeClass) {
    tr.appendChild(createMetricCell(typeRow?.DG_original, `${typeClass}-cell`));
    tr.appendChild(createMetricDeltaCell(typeRow?.DG_best, typeRow?.DG_original, `${typeClass}-cell`));
    tr.appendChild(createMetricCell(typeRow?.revenue_original, `${typeClass}-cell`));
    tr.appendChild(createMetricDeltaCell(typeRow?.revenue_best, typeRow?.revenue_original, `${typeClass}-cell`));
    tr.appendChild(createMetricCell(typeRow?.expense_original, `${typeClass}-cell`));
    tr.appendChild(createMetricDeltaCell(
        typeRow?.expense_best,
        typeRow?.expense_original,
        `${typeClass}-cell`,
        { preferLower: true }
    ));
    tr.appendChild(createOutlierCell(typeRow?.seg_outliers, `${typeClass}-cell`));
}

function createScenarioActionCell(summaryRow, activeWeek) {
    const td = document.createElement("td");
    td.className = "route-action-cell";

    const link = document.createElement("a");
    link.className = "open-link cta-link";
    link.href =
        `overview.html?label=${encodeURIComponent(summaryRow.label)}`
        + `&apr=${encodeURIComponent(summaryRow.apr_profile)}`
        + `&week=${encodeURIComponent(activeWeek)}`;
    link.title = "Open scenario";
    link.innerHTML = `
        <span>Open scenario</span>
        <span class="cta-link-icon">></span>
    `;

    td.appendChild(link);
    return td;
}

function createMergedCell(text, rowspan, className) {
    const td = document.createElement("td");
    td.rowSpan = rowspan;
    td.className = className;
    td.textContent = text;
    return td;
}

function createTextCell(text, className = "") {
    const td = document.createElement("td");
    td.className = className;
    td.textContent = text;
    return td;
}

function createMetricCell(value, className = "") {
    const td = document.createElement("td");
    td.className = `index-summary-table__metric ${className}`.trim();
    td.textContent = value == null ? "-" : fmtKr(value, 2);
    return td;
}

function createMetricDeltaCell(value, baseline, className = "", options = {}) {
    const td = document.createElement("td");
    td.className = `index-summary-table__metric ${className}`.trim();

    if (value == null || baseline == null) {
        td.textContent = "-";
        return td;
    }

    const deltaValue = value - baseline;
    const main = document.createElement("div");
    main.className = "index-summary-metric-main";
    main.textContent = fmtKr(value, 2);

    const delta = document.createElement("div");
    delta.className = `index-summary-metric-delta ${getDeltaClass(deltaValue, options)}`;
    delta.textContent = `(${formatSignedKr(deltaValue)})`;

    td.append(main, delta);
    return td;
}

function createOutlierCell(value, className = "") {
    const td = document.createElement("td");
    td.className = `index-summary-table__outliers ${className}`.trim();
    td.textContent = value == null ? "-" : Number(value).toLocaleString("en-US");
    return td;
}

function createFeedbackState(text) {
    const state = document.createElement("div");
    state.className = "index-summary-feedback";
    state.textContent = text;
    return state;
}

function countScenarioEntries(entries) {
    return new Set(entries.map(entry => `${entry.APR_profile}__${entry.label}`)).size;
}

function formatSignedKr(value) {
    const number = Number(value) || 0;
    const sign = number > 0 ? "+" : "";
    return `${sign}${fmtKr(number, 2)}`;
}

function getDeltaClass(value, options = {}) {
    const preferLower = options.preferLower === true;

    if (value > 0) {
        return preferLower ? "is-negative" : "is-positive";
    }
    if (value < 0) {
        return preferLower ? "is-positive" : "is-negative";
    }
    return "is-neutral";
}

function getOrderedValues(values, preferredOrder) {
    const unique = [...new Set(values)];
    const orderMap = new Map(preferredOrder.map((value, index) => [value, index]));

    return unique.sort((a, b) => {
        const aIndex = orderMap.has(a) ? orderMap.get(a) : Number.MAX_SAFE_INTEGER;
        const bIndex = orderMap.has(b) ? orderMap.get(b) : Number.MAX_SAFE_INTEGER;
        return aIndex - bIndex || String(a).localeCompare(String(b), "en", {
            sensitivity: "base"
        });
    });
}
