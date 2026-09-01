const DEFAULT_BASE_LAYER_CONFIG = {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    options: {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }
};

const MAP_STYLE_CONFIG = {
    color: {
        label: "Color",
        className: "fk-map-style-color"
    },
    bw: {
        label: "Light",
        className: "fk-map-style-bw"
    },
    dark: {
        label: "Dark",
        className: "fk-map-style-dark"
    }
};

export function createMapBaseLayer() {
    return L.tileLayer(
        DEFAULT_BASE_LAYER_CONFIG.url,
        DEFAULT_BASE_LAYER_CONFIG.options
    );
}

export function addMapStyleSelector(map, containerId, styleKeys = ["color", "bw", "dark"]) {
    const mapElement = document.getElementById(containerId);
    if (!mapElement) return;

    const host = mapElement.parentElement;
    if (!host) return;

    const toolbar = ensureMapToolbar(host, mapElement);
    if (toolbar.querySelector(".map-style-selector")) return;

    const selector = document.createElement("div");
    selector.className = "map-style-selector";

    styleKeys.forEach(key => {
        const config = MAP_STYLE_CONFIG[key];
        if (!config) return;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "map-style-button";
        button.textContent = config.label;
        button.dataset.styleKey = key;
        button.classList.toggle("active", map._fkActiveBaseStyle === key);
        button.addEventListener("click", () => {
            setMapStyle(map, key);
            selector.querySelectorAll(".map-style-button").forEach(btn => {
                btn.classList.toggle("active", btn.dataset.styleKey === key);
            });
        });
        selector.appendChild(button);
    });

    toolbar.appendChild(selector);
}

export function setMapStyle(map, styleKey) {
    const config = MAP_STYLE_CONFIG[styleKey];
    const mapContainer = map?.getContainer?.();
    if (!config || !mapContainer || map._fkActiveBaseStyle === styleKey) return;

    Object.values(MAP_STYLE_CONFIG).forEach(style => {
        mapContainer.classList.remove(style.className);
    });

    mapContainer.classList.add(config.className);
    map._fkActiveBaseStyle = styleKey;
}

function ensureMapToolbar(host, mapElement) {
    let toolbar = host.querySelector(".map-toolbar");
    if (!toolbar) {
        toolbar = document.createElement("div");
        toolbar.className = "map-toolbar";
        host.insertBefore(toolbar, mapElement);
    }

    const routeTypeSelector = host.querySelector(".route-type-selector");
    if (routeTypeSelector && routeTypeSelector.parentElement !== toolbar) {
        toolbar.appendChild(routeTypeSelector);
    }

    return toolbar;
}
