import { fmt, fmtKr } from "../utils/fmt.js";

export function renderKpiChangeCards(container, comparisons) {
    container.innerHTML = "";

    comparisons.forEach(comparison => {
        const card = document.createElement("article");
        card.className = "kpi-change-card";

        const status = getStatus(comparison.to.DG - comparison.from.DG);

        card.innerHTML = `
            <div class="kpi-change-card-header">
                <div>
                    <div class="kpi-change-eyebrow">Change</div>
                    <h3 class="kpi-change-title">${comparison.title}</h3>
                </div>
                <span class="kpi-change-chip ${status.className}">${status.label}</span>
            </div>
        `;

        const body = document.createElement("div");
        body.className = "kpi-change-card-body";

        body.appendChild(createMetricBlock({
            label: "Revenue",
            delta: comparison.to.revenue - comparison.from.revenue,
            percent: calcPercent(comparison.from.revenue, comparison.to.revenue),
            positiveIsGood: true,
            formatter: value => fmtKr(value, 2)
        }));

        body.appendChild(createMetricBlock({
            label: "Costs",
            delta: comparison.to.expense - comparison.from.expense,
            percent: calcPercent(comparison.from.expense, comparison.to.expense),
            positiveIsGood: false,
            formatter: value => fmtKr(value, 2)
        }));

        body.appendChild(createMetricBlock({
            label: "Contribution margin",
            delta: comparison.to.DG - comparison.from.DG,
            percent: calcPercent(comparison.from.DG, comparison.to.DG),
            positiveIsGood: true,
            formatter: value => fmtKr(value, 2)
        }));

        const meterDelta = comparison.to.lengthMeters - comparison.from.lengthMeters;
        if (comparison.from.lengthMeters !== 0 || comparison.to.lengthMeters !== 0) {
            body.appendChild(createMetricBlock({
                label: "Length (walk/bike)",
                delta: meterDelta,
                percent: calcPercent(comparison.from.lengthMeters, comparison.to.lengthMeters),
                positiveIsGood: false,
                formatter: value => fmt(value, "m", 0)
            }));
        }

        const secDelta = comparison.to.lengthSeconds - comparison.from.lengthSeconds;
        if (comparison.from.lengthSeconds !== 0 || comparison.to.lengthSeconds !== 0) {
            body.appendChild(createMetricBlock({
                label: "Length (driving)",
                delta: secDelta,
                percent: calcPercent(comparison.from.lengthSeconds, comparison.to.lengthSeconds),
                positiveIsGood: false,
                formatter: value => fmt(value, "sec", 0, "min")
            }));
        }

        card.appendChild(body);
        container.appendChild(card);
    });
}

function createMetricBlock({ label, delta, percent, positiveIsGood, formatter }) {
    const statusClass = getDeltaClass(delta, positiveIsGood);
    const block = document.createElement("div");
    const isPrimary = label === "Contribution margin";
    block.className = `kpi-change-metric${isPrimary ? " primary" : ""}`;

    const deltaText = formatter(delta);
    const signedDelta = delta > 0 ? `+${deltaText}` : deltaText;
    const percentText = percent === null
        ? "n/a"
        : `${percent > 0 ? "+" : ""}${formatPercent(percent)}`;

    block.innerHTML = `
        <div class="kpi-change-row">
            <span class="kpi-change-label">${label}</span>
            <div class="kpi-change-values">
                <span class="kpi-change-value ${statusClass}">${signedDelta}</span>
                <span class="kpi-change-percent ${statusClass}">${percentText}</span>
            </div>
        </div>
        <div class="kpi-change-bar">
            <span class="kpi-change-bar-fill ${statusClass}" style="width: ${barWidth(percent)}%"></span>
        </div>
    `;

    return block;
}

function calcPercent(from, to) {
    if (!Number.isFinite(from) || Math.abs(from) < 1e-9) {
        return null;
    }
    return ((to - from) / Math.abs(from)) * 100;
}

function formatPercent(value) {
    return `${Number(value).toLocaleString("en-US", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    })}%`;
}

function getDeltaClass(delta, positiveIsGood) {
    if (Math.abs(delta) < 1e-9) return "neutral";
    if (positiveIsGood) {
        return delta > 0 ? "positive" : "negative";
    }
    return delta < 0 ? "positive" : "negative";
}

function getStatus(delta) {
    if (Math.abs(delta) < 1e-9) {
        return { label: "Unchanged", className: "neutral" };
    }
    return delta > 0
        ? { label: "Better", className: "positive" }
        : { label: "Weaker", className: "negative" };
}

function barWidth(percent) {
    if (percent === null) return 0;
    if (Math.abs(percent) < 1e-9) return 0;
    return Math.max(8, Math.min(Math.abs(percent) * 4, 100));
}
