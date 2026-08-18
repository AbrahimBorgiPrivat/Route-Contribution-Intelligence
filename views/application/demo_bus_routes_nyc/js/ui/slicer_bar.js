/**
 * Build slicer bar (Label / Profile / Analysis period)
 * @param {HTMLElement} container
 * @param {Object} options
 * @param {Array<string>} options.labels
 * @param {Array<string>} options.aprs
 * @param {Array<string>} options.weeks
 * @param {Function} options.onChange (receives {label, apr, week})
 */
export function renderSlicerBar(container, { labels, aprs, weeks, onChange }) {
    container.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "slicer-bar";

    function createSelect(id, title, values) {
        const wrap = document.createElement("div");
        wrap.className = "slicer-wrap";

        const label = document.createElement("label");
        label.textContent = title;

        const select = document.createElement("select");
        select.id = id;
        select.className = "slicer-select";

        const allOption = document.createElement("option");
        allOption.value = "";
        allOption.textContent = "All";
        select.appendChild(allOption);

        values.forEach(v => {
            const o = document.createElement("option");
            o.value = v;
            o.textContent = v;
            select.appendChild(o);
        });

        wrap.appendChild(label);
        wrap.appendChild(select);
        return { wrap, select };
    }

    const labelSelect = createSelect("slicer-label", "Label", labels);
    const aprSelect = createSelect("slicer-apr", "Profile", aprs);
    const weekSelect = createSelect("slicer-week", "Analysis period", weeks);

    wrapper.appendChild(labelSelect.wrap);
    wrapper.appendChild(aprSelect.wrap);
    wrapper.appendChild(weekSelect.wrap);

    container.appendChild(wrapper);

    function emitChange() {
        onChange({
            label: labelSelect.select.value || null,
            apr: aprSelect.select.value || null,
            week: weekSelect.select.value || null
        });
    }

    labelSelect.select.addEventListener("change", emitChange);
    aprSelect.select.addEventListener("change", emitChange);
    weekSelect.select.addEventListener("change", emitChange);
}
