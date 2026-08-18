from typing import List, Dict, Any, Optional, Literal
from tqdm import tqdm
from libraries.classes.osm_segment_api import OSMSegmentClient

def snap_points_with_units(
    points: List[Dict[str, float]],
    *,
    address_number: Optional[List[int]] = None,
    show_progress: bool = True,
    allowed_highways: List[str] = [
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "living_street",
            ],
    max_batch_size: int = None,
    input_crs: str = "EPSG:4326",
    output_crs: str = "EPSG:4326",
    x_key: str = "x",
    y_key: str = "y",
    chunk_size: int | None = None,
    use_rotated_side: bool = False,
    offset_m: float = 4.5,
    entry_angle_deg: float = -60.0,
    exit_angle_deg: float = 60.0,
    ) -> List[Dict[str, Any]]:
    """
    Snap a sequence of points and assign structural units.

    Returns a list of dicts aligned 1:1 with `points`, each containing:
        - segment_id
        - side_of_road
        - unit_number
        - unit_start_point_lon / lat
        - unit_end_point_lon / lat
    """
    if address_number is not None and len(address_number) != len(points):
        raise ValueError(
            "address_number must be None or have same length as points"
        )
    client = OSMSegmentClient(
            base_url = "local",
            input_crs = input_crs,
            output_crs = output_crs,
            allowed_highways = allowed_highways,
        )
    if max_batch_size is not None:
            client.MAX_BATCH_SIZE = max_batch_size
    # --------------------------------------------------
    # 1. Batch snap
    # --------------------------------------------------
    results = client.snap_nearest_batch(
        points,
        show_progress=show_progress,
        x_key=x_key,
        y_key=y_key,
        chunk_size=chunk_size,
    )
    visited_units: List[Dict[str, Any]] = []
    unit_number = -1
    enriched_rows: List[Dict[str, Any]] = []
    # --------------------------------------------------
    # 2. Process each snapped result
    # --------------------------------------------------
    iterator = tqdm(results, desc="Assigning OSM units", leave=False)
    for i, r in enumerate(iterator):
        segment_id = r["segment"]["segment_id"]
        raw_side = r["geometry"].get("side_of_road")
        if raw_side in {"left", "right"}:
            resolved_side = raw_side
        else:
            if address_number is not None:
                resolved_side = (
                    "left" if address_number[i] % 2 == 1 else "right"
                )
            else:
                resolved_side = "right"
        matched_unit = None
        # ----------------------------------------------
        # 2a. Try to reuse an existing unit
        # ----------------------------------------------
        for unit in visited_units:
            if (
                segment_id in unit["visited_segments"]
                and resolved_side  == unit["side_of_road"]
            ):
                matched_unit = unit
                break
        # ----------------------------------------------
        # 2b. Create new unit if needed
        # ----------------------------------------------
        if matched_unit is None:
            group = client.group_segments_on_side(
                r,
                allowed_highways=allowed_highways,
                side_of_road=resolved_side,         
                use_rotated_side = use_rotated_side,
                offset_m = offset_m,
                entry_angle_deg = entry_angle_deg,
                exit_angle_deg = exit_angle_deg,
            )
            unit_number += 1
            start_point = group["start_point"]
            end_point = group["end_point"]
            if resolved_side == "left":
                start_point, end_point = end_point, start_point
            matched_unit = {
                "unit_number": unit_number,
                "side_of_road": resolved_side,
                "visited_segments": group["visited_segments"],
                "start_point": start_point,
                "end_point": end_point,
            }
            visited_units.append(matched_unit)
        # ----------------------------------------------
        # 3. Emit row-level enrichment
        # ----------------------------------------------
        enriched_rows.append(
            {
                "segment_id": segment_id,
                "side_of_road": resolved_side,
                "unit_number": matched_unit["unit_number"],
                "unit_start_point_lon": matched_unit["start_point"]["lon"],
                "unit_start_point_lat": matched_unit["start_point"]["lat"],
                "unit_end_point_lon": matched_unit["end_point"]["lon"],
                "unit_end_point_lat": matched_unit["end_point"]["lat"],
            }
        )
    return enriched_rows
