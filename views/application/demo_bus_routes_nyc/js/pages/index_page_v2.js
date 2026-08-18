import { el } from "../utils/dom.js";
import { loadRegistry } from "../data/load_registry.js";
import { renderHierarchy } from "../ui/hierarchy_renderer.js";

(async function () {

    const registry = await loadRegistry();
    const container = el("hierarchy-container");
    await renderHierarchy(container, { registry });

})();
