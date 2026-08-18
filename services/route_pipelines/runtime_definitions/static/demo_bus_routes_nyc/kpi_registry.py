from typing import Any, Dict


def route_id(row: Dict[str, Any]):
    return row.get("route_id")


def L_original(row: Dict[str, Any]):
    return row.get("L_original")


def L_opt(row: Dict[str, Any]):
    return row.get("L_opt")


def DG_original(row: Dict[str, Any]):
    return row.get("DG_original")


def DG_best(row: Dict[str, Any]):
    return row.get("DG_best")


def count_outliers(row: Dict[str, Any]):
    outliers = row.get("S_outlier")
    return len(outliers) if outliers is not None else None


KPI_REGISTRY = {
    "route_id": route_id,
    "L_original": L_original,
    "L_opt": L_opt,
    "DG_original": DG_original,
    "DG_best": DG_best,
    "count_outliers": count_outliers,
}
