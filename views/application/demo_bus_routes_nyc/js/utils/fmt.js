/**
 * Format numeric values with optional unit and decimals.
 * If value is null/undefined/NaN, returns "-".
 */
export function fmt(value, unit = "", decimals = 0, timeunit = "sec") {
    if (value === null || value === undefined || isNaN(Number(value))) {
        return "-";
    }
    if (unit === "kr") {
        return fmtKr(value, decimals);
    }
    let num = Number(value);
    let displayUnit = unit;
    if (unit === "sec") {
        if (timeunit === "min") {
            num = num / 60;
            displayUnit = "min";
        } else if (timeunit === "hour") {
            num = num / 3600;
            displayUnit = "hour";
        }
    }
    const formatted = num.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
    return `${formatted}${displayUnit ? " " + displayUnit : ""}`;
}
export function fmtKr(value, decimals = 0) {
    if (value == null || value === undefined || isNaN(Number(value))) return "-";
    const num = Number(value);
    return `$${num.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    })}`;
}

export function fmtMeters(value, decimals = 0) {
    return fmt(value, "m", decimals);
}
