/**
 * Pre-declared empty LayerGroups for all route + marker types.
 */

export const ROUTE_LAYERS = {
    "T1 Original": L.layerGroup(),
    "T1 Optimal": L.layerGroup(),
    "T2 Original": L.layerGroup(),
    "T2 Optimal": L.layerGroup()
};

export const MARKER_LAYERS = {
    "T1 Normal": L.layerGroup(),
    "T1 Outlier": L.layerGroup(),
    "T1 Significant": L.layerGroup(),
    "T2 Normal": L.layerGroup(),
    "T2 Outlier": L.layerGroup(),
    "T2 Significant": L.layerGroup()
};

/**
 * Color palette for each route type.
 */
export const ROUTE_COLORS = {
    "T1 Original": "#004B6B",
    "T1 Optimal": "#0094C6",
    "T2 Original": "#C65F00",
    "T2 Optimal": "#FF8900"
};

export const MARKER_COLORS = {
    "T1 Normal":      "#0094C6",
    "T1 Outlier":     "#FF7F1A",
    "T1 Significant": "#7A0000",
    "T2 Normal":      "#0094C6",
    "T2 Outlier":     "#FF7F1A",
    "T2 Significant": "#7A0000"
};