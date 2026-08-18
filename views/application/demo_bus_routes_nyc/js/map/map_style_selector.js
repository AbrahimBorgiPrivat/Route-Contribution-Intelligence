const MAP_STYLE_CONFIG = {
    color: {
        label: "Color",
        url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        options: {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }
    },
    bw: {
        label: "Light",
        url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        options: {
            maxZoom: 20,
            subdomains: "abcd",
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> ' +
                '&copy; <a href="https://carto.com/attributions">CARTO</a>'
        }
    },
    dark: {
        label: "Dark",
        url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        options: {
            maxZoom: 20,
            subdomains: "abcd",
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> ' +
                '&copy; <a href="https://carto.com/attributions">CARTO</a>'
        }
    }
};

export function createMapBaseLayers() {
    return Object.fromEntries(
        Object.entries(MAP_STYLE_CONFIG).map(([key, config]) => [key, L.tileLayer(config.url, config.options)])
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
        const layer = map._fkBaseLayers?.[key];
        if (!config || !layer) return;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "map-style-button";
        button.textContent = config.label;
        button.dataset.styleKey = key;
        button.classList.toggle("active", map._fkActiveBaseLayer === key);
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
    const nextLayer = map._fkBaseLayers?.[styleKey];
    if (!nextLayer || map._fkActiveBaseLayer === styleKey) return;

    const currentLayer = map._fkBaseLayers?.[map._fkActiveBaseLayer];
    if (currentLayer && map.hasLayer(currentLayer)) {
        map.removeLayer(currentLayer);
    }

    nextLayer.addTo(map);
    map._fkActiveBaseLayer = styleKey;
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
