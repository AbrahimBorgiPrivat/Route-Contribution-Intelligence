import { loadRouteJsonCached } from "../data/load_route_json_cached.js";
import { extractRouteKPIsV2 } from "../data/extract_route_kpis_v2.js";
import { aggregateKPIs } from "../data/aggregate_kpis.js";
import { renderKpiCard } from "./kpi_cards.js";
import { renderKpiChangeCards } from "./kpi_change_cards.js";
import { renderScenarioIndexSummary } from "./scenario_index_summary.js";

export async function renderHierarchy(container, { registry }) {
    container.innerHTML = "";

    const slicerBar = document.createElement("div");
    slicerBar.className = "table-filter-bar slicer-bar";
    container.appendChild(slicerBar);

    const labels = [...new Set(registry.map(r => r.label))].sort(compareLabels);
    const aprs = [...new Set(registry.map(r => r.APR_profile))];
    const weeksAll = [...new Set(registry.map(r => r.Week_Profile))];

    function createSelect(title, values) {
        const selectedValues = new Set();

        const wrap = document.createElement("div");
        wrap.className = "table-filter";

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
        search.placeholder = `Search ${title.toLowerCase()}`;

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

        const optionsWrap = document.createElement("div");
        optionsWrap.className = "table-filter-options";

        const optionItems = values.map(value => buildOption(value));
        optionItems.forEach(({ element }) => optionsWrap.appendChild(element));

        const empty = document.createElement("div");
        empty.className = "table-filter-empty hidden";
        empty.textContent = "No results";
        optionsWrap.appendChild(empty);

        function buildOption(value) {
            const option = document.createElement("label");
            option.className = "table-filter-option";
            option.dataset.value = value.toLowerCase();

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = value;

            const text = document.createElement("span");
            text.textContent = value;

            checkbox.addEventListener("change", () => {
                if (checkbox.checked) {
                    selectedValues.add(value);
                } else {
                    selectedValues.delete(value);
                }
                updateSummary();
                renderFiltered();
            });

            option.appendChild(checkbox);
            option.appendChild(text);
            return { element: option, checkbox, value };
        }

        function updateSummary() {
            const summary = triggerText.querySelector(".table-filter-summary");
            if (selectedValues.size === 0) {
                summary.textContent = "All";
                return;
            }
            if (selectedValues.size <= 2) {
                summary.textContent = [...selectedValues].join(", ");
                return;
            }
            summary.textContent = `${selectedValues.size} selected`;
        }

        function filterOptions() {
            const term = search.value.trim().toLowerCase();
            let visibleCount = 0;

            optionItems.forEach(({ element }) => {
                const isVisible = !term || element.dataset.value.includes(term);
                element.classList.toggle("hidden", !isVisible);
                if (isVisible) visibleCount += 1;
            });
            empty.classList.toggle("hidden", visibleCount !== 0);
        }

        trigger.addEventListener("click", () => {
            const isHidden = panel.classList.contains("hidden");
            document.querySelectorAll(".table-filter-panel").forEach(el => el.classList.add("hidden"));
            if (isHidden) {
                panel.classList.remove("hidden");
                search.focus();
            }
        });

        search.addEventListener("input", filterOptions);

        selectAllBtn.addEventListener("click", () => {
            optionItems.forEach(({ checkbox, value }) => {
                checkbox.checked = true;
                selectedValues.add(value);
            });
            updateSummary();
            renderFiltered();
        });

        clearBtn.addEventListener("click", () => {
            optionItems.forEach(({ checkbox, value }) => {
                checkbox.checked = false;
                selectedValues.delete(value);
            });
            updateSummary();
            renderFiltered();
        });

        document.addEventListener("click", e => {
            if (!wrap.contains(e.target)) {
                panel.classList.add("hidden");
            }
        });

        panel.appendChild(search);
        panel.appendChild(actions);
        panel.appendChild(optionsWrap);

        wrap.appendChild(trigger);
        wrap.appendChild(panel);
        slicerBar.appendChild(wrap);

        updateSummary();

        return {
            get values() {
                return selectedValues;
            }
        };
    }

    const selLabel = createSelect("Label", labels);
    const selApr = createSelect("Profile", aprs);
    const selWeek = createSelect("Analysis period", weeksAll);

    const summaryWrap = document.createElement("div");
    container.appendChild(summaryWrap);

    const contentWrap = document.createElement("div");
    container.appendChild(contentWrap);

    function renderFiltered() {
        const filtered = filterRegistryEntries(registry, {
            labels: selLabel.values,
            aprs: selApr.values,
            weeks: selWeek.values
        });

        renderScenarioIndexSummary(summaryWrap, {
            entries: filtered,
            aprOrder: aprs,
            weekOrder: weeksAll,
            compareLabels
        });

        renderLabelBlocks(contentWrap, filtered);
    }

    renderFiltered();
}

function filterRegistryEntries(registry, selections) {
    return registry.filter(entry =>
        matchesSelection(selections.labels, entry.label)
        && matchesSelection(selections.aprs, entry.APR_profile)
        && matchesSelection(selections.weeks, entry.Week_Profile)
    );
}

function matchesSelection(selectedValues, value) {
    return selectedValues.size === 0 || selectedValues.has(value);
}

function renderLabelBlocks(root, filteredRegistry) {
    root.innerHTML = "";

    const filteredLabels = [...new Set(filteredRegistry.map(r => r.label))]
        .sort(compareLabels);

    for (const label of filteredLabels) {
        renderLabelBlock(root, filteredRegistry, label);
    }
}

function compareLabels(a, b) {
    return getLabelPriority(a) - getLabelPriority(b)
        || a.localeCompare(b, "en", { sensitivity: "base" });
}

function getLabelPriority(label) {
    const value = String(label || "").toLowerCase();
    if (value === "all routes") return 0;
    return 1;
}

function renderLabelBlock(root, registry, label) {
    const wrapper = document.createElement("div");
    wrapper.className = "hier-label";

    const header = document.createElement("div");
    header.className = "hier-label-header";
    header.innerHTML = `<h2 style="margin:0;">${label}</h2>`;

    const content = document.createElement("div");
    content.className = "collapsible-content";

    wrapper.appendChild(header);
    wrapper.appendChild(content);
    root.appendChild(wrapper);

    const labelEntries = registry.filter(r => r.label === label);
    const aprs = [...new Set(labelEntries.map(r => r.APR_profile))];

    for (const apr of aprs) {
        renderProfileBlock(content, labelEntries, label, apr);
    }
}

function renderProfileBlock(root, labelEntries, label, apr) {
    const wrapper = document.createElement("div");
    wrapper.className = "hier-profile";

    const header = document.createElement("div");
    header.className = "collapsible-header profile-header";
    header.innerHTML = `<h3 style="margin:0;">${apr}</h3>`;

    const content = document.createElement("div");
    content.className = "collapsible-content hidden";

    let initialized = false;

    header.addEventListener("click", () => {
        const wasHidden = content.classList.contains("hidden");

        content.classList.toggle("hidden");
        header.classList.toggle("collapsed");

        if (wasHidden && !initialized) {
            const aprEntries = labelEntries.filter(r => r.APR_profile === apr);
            const weeks = [...new Set(aprEntries.map(r => r.Week_Profile))];

            if (weeks.length) {
                renderWeekSelector(content, aprEntries, label, apr, weeks);
                initialized = true;
            }
        }
    });

    wrapper.appendChild(header);
    wrapper.appendChild(content);
    root.appendChild(wrapper);
}

function renderWeekSelector(root, aprEntries, label, apr, weeks) {
    let selectedIndex = 0;

    const headerRow = document.createElement("div");
    headerRow.className = "week-header";

    const weekTitle = document.createElement("div");
    weekTitle.className = "week-title";

    const weekLink = document.createElement("a");
    weekLink.className = "week-link";

    headerRow.appendChild(weekTitle);
    headerRow.appendChild(weekLink);
    root.appendChild(headerRow);

    const navRow = document.createElement("div");
    navRow.className = "week-nav-row";

    const btnPrev = document.createElement("button");
    btnPrev.className = "week-arrow";
    btnPrev.textContent = "<";

    const btnNext = document.createElement("button");
    btnNext.className = "week-arrow";
    btnNext.textContent = ">";

    const kpiStack = document.createElement("div");
    kpiStack.className = "week-kpi-stack";

    const loadingState = document.createElement("div");
    loadingState.className = "async-feedback hidden";

    const changeGrid = document.createElement("div");
    changeGrid.className = "kpi-change-grid";

    const kpiGrid = document.createElement("div");
    kpiGrid.className = "kpi-grid";

    kpiStack.appendChild(loadingState);
    kpiStack.appendChild(changeGrid);
    kpiStack.appendChild(kpiGrid);

    navRow.appendChild(btnPrev);
    navRow.appendChild(kpiStack);
    navRow.appendChild(btnNext);
    root.appendChild(navRow);

    const pillRow = document.createElement("div");
    pillRow.className = "week-pill-row";
    root.appendChild(pillRow);

    weeks.forEach((w, i) => {
        const pill = document.createElement("button");
        pill.className = "week-pill";
        pill.textContent = w;
        pill.addEventListener("click", () => showWeek(i));
        pillRow.appendChild(pill);
    });

    async function showWeek(index) {
        selectedIndex = (index + weeks.length) % weeks.length;
        const activeWeek = weeks[selectedIndex];

        pillRow.querySelectorAll(".week-pill").forEach((btn, i) => {
            btn.classList.toggle("active", i === selectedIndex);
        });

        weekTitle.textContent = activeWeek;

        weekLink.textContent = "Open";
        weekLink.href =
            `overview.html?label=${encodeURIComponent(label)}`
            + `&apr=${encodeURIComponent(apr)}`
            + `&week=${encodeURIComponent(activeWeek)}`;

        const weekEntries = aprEntries.filter(e => e.Week_Profile === activeWeek);
        loadingState.textContent = "Calculating scenario...";
        loadingState.classList.remove("hidden");
        changeGrid.innerHTML = "";
        kpiGrid.innerHTML = "";

        const routeJsons = await Promise.all(
            weekEntries.map(e => loadRouteJsonCached(e.route_json))
        );

        const routeKPIs = routeJsons.map(extractRouteKPIsV2);
        const type1Agg = aggregateKPIs(routeKPIs, true);
        const type2Agg = aggregateKPIs(routeKPIs, false);

        loadingState.classList.add("hidden");
        renderKpiChangeCards(changeGrid, [
            {
                title: "Type 1 (Original) -> Type 1 (Optimized)",
                from: {
                    revenue: type1Agg.revenue_original,
                    expense: type1Agg.expense_original,
                    DG: type1Agg.DG_original,
                    lengthMeters: type1Agg.L_original_m,
                    lengthSeconds: type1Agg.L_original_sec
                },
                to: {
                    revenue: type1Agg.revenue_best,
                    expense: type1Agg.expense_best,
                    DG: type1Agg.DG_best,
                    lengthMeters: type1Agg.L_opt_m,
                    lengthSeconds: type1Agg.L_opt_sec
                }
            },
            {
                title: "Type 1 (Original) -> Type 2 (Original)",
                from: {
                    revenue: type1Agg.revenue_original,
                    expense: type1Agg.expense_original,
                    DG: type1Agg.DG_original,
                    lengthMeters: type1Agg.L_original_m,
                    lengthSeconds: type1Agg.L_original_sec
                },
                to: {
                    revenue: type2Agg.revenue_original,
                    expense: type2Agg.expense_original,
                    DG: type2Agg.DG_original,
                    lengthMeters: type2Agg.L_original_m,
                    lengthSeconds: type2Agg.L_original_sec
                }
            },
            {
                title: "Type 2 (Original) -> Type 2 (Optimized)",
                from: {
                    revenue: type2Agg.revenue_original,
                    expense: type2Agg.expense_original,
                    DG: type2Agg.DG_original,
                    lengthMeters: type2Agg.L_original_m,
                    lengthSeconds: type2Agg.L_original_sec
                },
                to: {
                    revenue: type2Agg.revenue_best,
                    expense: type2Agg.expense_best,
                    DG: type2Agg.DG_best,
                    lengthMeters: type2Agg.L_opt_m,
                    lengthSeconds: type2Agg.L_opt_sec
                }
            },
            {
                title: "Type 1 (Original) -> Type 2 (Optimized)",
                from: {
                    revenue: type1Agg.revenue_original,
                    expense: type1Agg.expense_original,
                    DG: type1Agg.DG_original,
                    lengthMeters: type1Agg.L_original_m,
                    lengthSeconds: type1Agg.L_original_sec
                },
                to: {
                    revenue: type2Agg.revenue_best,
                    expense: type2Agg.expense_best,
                    DG: type2Agg.DG_best,
                    lengthMeters: type2Agg.L_opt_m,
                    lengthSeconds: type2Agg.L_opt_sec
                }
            }
        ]);

        renderKpiCard(kpiGrid, "Type 1 (Fixed route)", type1Agg);
        renderKpiCard(kpiGrid, "Type 2 (Optimized route)", type2Agg);
    }

    btnPrev.addEventListener("click", () => showWeek(selectedIndex - 1));
    btnNext.addEventListener("click", () => showWeek(selectedIndex + 1));
    showWeek(0);
}
