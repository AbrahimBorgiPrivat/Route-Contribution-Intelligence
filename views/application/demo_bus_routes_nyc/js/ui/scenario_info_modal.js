import { getScenarioExplanation } from "../data/load_scenario_metadata.js";

const FALLBACK_EXPLANATION = "No explanation has been added for this selection yet.";

function getModalElements(triggerId, modalId) {
    const trigger = document.getElementById(triggerId);
    const modal = document.getElementById(modalId);
    const closeButton = modal?.querySelector(".scenario-info-modal__close");
    const content = modal?.querySelector("[data-scenario-info-content]");

    return {
        trigger,
        modal,
        closeButton,
        content,
    };
}

function getExplanationOrFallback(metadata, type, key) {
    return getScenarioExplanation(metadata, type, key) ?? FALLBACK_EXPLANATION;
}

function buildSection(title, value, explanation) {
    const section = document.createElement("section");
    section.className = "scenario-info-section";

    const heading = document.createElement("h3");
    heading.className = "scenario-info-section__title";
    heading.textContent = title;

    const valueLine = document.createElement("p");
    valueLine.className = "scenario-info-section__value";
    valueLine.textContent = value;

    const body = document.createElement("p");
    body.className = "scenario-info-section__text";
    body.textContent = explanation;

    section.append(heading, valueLine, body);
    return section;
}

function buildSections(metadata, { label, apr, week }) {
    return [
        buildSection("Label", label, getExplanationOrFallback(metadata, "labels", label)),
        buildSection("Profile", apr, getExplanationOrFallback(metadata, "APR_profiles", apr)),
        buildSection("Analysis period", week, getExplanationOrFallback(metadata, "week_profiles", week)),
    ];
}

function renderSections(content, sections) {
    content.replaceChildren(...sections);
}

function openModal(modal, closeButton) {
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("scenario-info-open");
    closeButton.focus();
}

function closeModal(modal, trigger) {
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("scenario-info-open");
    trigger.focus();
}

function registerEvents({ trigger, modal, closeButton }) {
    trigger.addEventListener("click", () => {
        openModal(modal, closeButton);
    });

    modal.addEventListener("click", event => {
        const shouldClose = event.target instanceof HTMLElement &&
            event.target.dataset.scenarioInfoClose === "true";

        if (shouldClose) {
            closeModal(modal, trigger);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !modal.hidden) {
            closeModal(modal, trigger);
        }
    });
}

export function initializeScenarioInfoModal({
    metadata,
    label,
    apr,
    week,
    triggerId = "scenario-info-trigger",
    modalId = "scenario-info-modal",
}) {
    const { trigger, modal, closeButton, content } = getModalElements(triggerId, modalId);

    if (!trigger || !modal || !closeButton || !content) {
        return;
    }

    const sections = buildSections(metadata, { label, apr, week });
    renderSections(content, sections);
    registerEvents({ trigger, modal, closeButton });
}
