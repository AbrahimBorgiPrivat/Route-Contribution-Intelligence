import json
from pathlib import Path
from typing import Dict, FrozenSet, Any
import base64
import pickle

# ============================================================
# Internal serialization utilities
# ============================================================

def _fs_to_key(S: FrozenSet[int]) -> str:
    return ";".join(map(str, sorted(S)))  # empty set => ""


def _key_to_fs(k: str) -> FrozenSet[int]:
    if k == "":
        return frozenset()
    return frozenset(int(x) for x in k.split(";"))


def _serialize_fs_dict(d: Dict[FrozenSet[int], float]) -> Dict[str, float]:
    return {_fs_to_key(S): float(v) for S, v in d.items()}


def _deserialize_fs_dict(d: Dict[str, float]) -> Dict[FrozenSet[int], float]:
    return {_key_to_fs(k): float(v) for k, v in d.items()}

def _b64_pickle(obj: Any) -> str:
    return base64.b64encode(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)).decode("ascii")

def _unb64_pickle(s: str) -> Any:
    return pickle.loads(base64.b64decode(s.encode("ascii")))

# ============================================================
# File path resolution
# ============================================================

def _get_cache_file_path(
    *,
    base_path: str,
    label: str,
    route_id: Any,
    strict: bool,
) -> Path:
    """
    Returns:
        .../data/<label>/<route_id>/c_distances_type1.json
        .../data/<label>/<route_id>/c_distances_type2.json
    """
    file_name = "c_distances_type1.json" if strict else "c_distances_type2.json"

    return (
        Path(base_path)
        / "data"
        / label
        / str(route_id)
        / file_name
    )


# ============================================================
# Public API
# ============================================================
def cache_exists(
    *,
    base_path: str,
    label: str,
    route_id: Any,
    strict: bool,
) -> bool:
    return _get_cache_file_path(
        base_path=base_path,
        label=label,
        route_id=route_id,
        strict=strict,
    ).exists()

def load_cache(*, base_path: str, label: str, route_id: Any, strict: bool) -> Dict[str, Any]:
    path = _get_cache_file_path(base_path=base_path, label=label, route_id=route_id, strict=strict)
    with open(path, "r") as f:
        raw = json.load(f)

    structured = raw.get("structured_blob")  # optional
    structured_loaded = None
    if structured is not None:
        structured_loaded = {k: _unb64_pickle(v) if v is not None else None for k, v in structured.items()}

    return {
        "C_distance_full": _deserialize_fs_dict(raw["C_distance_full"]),
        "R_seq": raw["R_seq"],
        "L_R": float(raw["L_R"]),
        "structured": structured_loaded,  # dict or None
        "inner_solver": raw.get("inner_solver"),
    }

def save_cache(
    base_path: str,
    label: str,
    route_id: Any,
    strict: bool,
    C_distance_full: Dict[FrozenSet[int], float],
    R_seq,
    L_R: float,
    *,
    D_outer=None,
    D_all=None,
    inner_models=None,
    inner_solver=None,
    inner_cache=None,
    outer_cache=None,
) -> None:
    path = _get_cache_file_path(base_path=base_path, label=label, route_id=route_id, strict=strict)
    path.parent.mkdir(parents=True, exist_ok=True)

    structured_blob = None
    if any(x is not None for x in (D_outer, D_all, inner_models, inner_cache, outer_cache)):
        structured_blob = {
            "D_outer": _b64_pickle(D_outer) if D_outer is not None else None,
            "D_all": _b64_pickle(D_all) if D_all is not None else None,
            "inner_models": _b64_pickle(inner_models) if inner_models is not None else None,
            "inner_cache": _b64_pickle(inner_cache) if inner_cache is not None else None,
            "outer_cache": _b64_pickle(outer_cache) if outer_cache is not None else None,
        }

    payload = {
        "C_distance_full": _serialize_fs_dict(C_distance_full),
        "R_seq": R_seq,
        "L_R": float(L_R),
        "inner_solver": inner_solver,
        "structured_blob": structured_blob,
    }

    with open(path, "w") as f:
        json.dump(payload, f)
