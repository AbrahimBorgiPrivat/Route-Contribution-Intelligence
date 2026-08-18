/*
Leaflet.TextPath 1.2.3 - https://github.com/makinacorpus/Leaflet.TextPath
*/

L.TextPath = {};
L.TextPath.VERSION = "1.2.3";

(function () {
    const originalContainsPoint = L.Path.prototype._containsPoint;
    L.Path.include({
        _containsPoint: function (p) {
            if (this.options.text) return false;
            return originalContainsPoint.call(this, p);
        }
    });
})();

L.Polyline.include({
    setText: function (text, options) {
        if (typeof text === "string") {
            this._text = text;
        } else {
            return this;
        }
    }
});

L.Polyline.include({
    _originalUpdatePath: L.Polyline.prototype._updatePath,
    _updatePath: function () {
        this._originalUpdatePath();
        this._updateText();
    },
    _updateText: function () {
        if (!this._text || !this._renderer || !this._map) return;
        const container = this._renderer._container;
        if (!container) return;
        const updateText = this._renderer._updateText;
        this._renderer._updateText = updateText;
        this._renderer._updateText(this);
    }
});

L.SVG.include({
    _updateText: function (layer) {
        const text = layer._text;
        if (!text) return;
        // Do not apply text to circle markers etc.
        if (layer._radius) return;
        if (!this._textRoot) {
            this._textRoot = document.createElementNS("http://www.w3.org/2000/svg", "g");
            this._container.appendChild(this._textRoot);
        }
        const root = this._textRoot;
        const existing = root.querySelector("#textpath-" + layer._leaflet_id);
        if (existing) root.removeChild(existing);
        // Build path (the geometry)
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("id", "textpath-" + layer._leaflet_id);
        let d = "M ";
        layer._parts.forEach(function (part) {
            for (let i = 0; i < part.length; i++) {
                d += part[i].x + " " + part[i].y + " ";
            }
        });
        path.setAttribute("d", d.trim());
        // Build text and textPath
        const textNode = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const textPath = document.createElementNS("http://www.w3.org/2000/svg", "textPath");
        textPath.setAttribute("href", "#textpath-" + layer._leaflet_id);
        textPath.setAttribute("startOffset", "0%");
        textPath.setAttribute("dominant-baseline", "central");
        const options = layer.options.textOptions || {};
        for (let key in options) {
            textPath.setAttribute(key, options[key]);
        }
        textPath.textContent = text;
        textNode.appendChild(textPath);
        root.appendChild(path);
        root.appendChild(textNode);
    }

});
