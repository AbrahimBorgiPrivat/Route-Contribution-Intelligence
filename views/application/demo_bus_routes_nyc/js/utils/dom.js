/**
 * Shorthand for document.getElementById.
 */
export function el(id) {
    return document.getElementById(id);
}

/**
 * Insert HTML at the end of an element.
 */
export function appendHtml(element, html) {
    if (!element) return;
    element.insertAdjacentHTML("beforeend", html);
}

/**
 * Replace element contents with HTML.
 */
export function setHtml(element, html) {
    if (!element) return;
    element.innerHTML = html;
}
