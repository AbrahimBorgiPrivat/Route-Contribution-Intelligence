from __future__ import annotations

from pathlib import Path


def route_output_exists(
    *,
    save_root: str | Path,
    label_name: str,
    route_id: str | int,
    apr_label: str,
    week_label: str,
) -> bool:
    target_dir = (
        Path(save_root)
        / label_name
        / str(route_id)
        / apr_label
        / week_label
    )
    return target_dir.exists()
