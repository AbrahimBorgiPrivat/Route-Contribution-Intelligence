import pandas as pd
import pyproj
import os
from typing import Dict, List, Any, Optional, Set

from libraries.config import STRUCTURED_PROBLEM_TYPES_SET, PROBLEM_TYPES, PROBLEM_TYPES_SET
from libraries.utils.preprocessing.osm_segments.osm_snap_points_with_units import snap_points_with_units
from libraries.classes.osrm_api import OSRMClient

def attach_revenue_data(
    df: pd.DataFrame,
    col_map: Dict[str, Any],
) -> pd.DataFrame:
    """
    Attach revenue information to the dataset based on configuration in col_map.

    Expected in col_map["revenue"]:
        {
            "path_revenue": str,
            "join_fields": { "<df_col>": "<rev_col>", ... },
            "rev_fields": [ "<rev_col_1>", ..., "<rev_col_n>" ],
            "rev_formula": "AVG" | "SUM" | "MEDIAN" | "MIN" | "MAX",
            "rev_include_all_addresses": bool
        }
    """
    # ------------------------------------------------------------
    # 0. Check if revenue config exists
    # ------------------------------------------------------------
    rev_cfg = col_map.get("revenue")
    if rev_cfg is None:
        return df
    # ------------------------------------------------------------
    # 1. Validate revenue path
    # ------------------------------------------------------------
    path_revenue = rev_cfg.get("path_revenue")
    if not path_revenue:
        return df
    if not os.path.exists(path_revenue):
        raise FileNotFoundError(f"Revenue data file does not exist: {path_revenue}")
    # ------------------------------------------------------------
    # 2. Load revenue CSV
    # ------------------------------------------------------------
    seperator = rev_cfg.get("sep",";")
    rev_df = pd.read_csv(path_revenue, sep=seperator)
    # ------------------------------------------------------------
    # 3. Validate join fields
    # ------------------------------------------------------------
    join_fields: Dict[str, str] = rev_cfg.get("join_fields", {})
    if not join_fields:
        raise ValueError("Revenue config must define 'join_fields'.")
    for df_col, rev_col in join_fields.items():
        if df_col not in df.columns:
            raise KeyError(f"Join column '{df_col}' does not exist in dataset.")
        if rev_col not in rev_df.columns:
            raise KeyError(f"Join column '{rev_col}' does not exist in revenue data.")
    # ------------------------------------------------------------
    # 4. Validate revenue fields
    # ------------------------------------------------------------
    rev_fields: List[str] = rev_cfg.get("rev_fields", [])
    if not rev_fields:
        raise ValueError("Revenue config must define 'rev_fields'.")
    missing = [c for c in rev_fields if c not in rev_df.columns]
    if missing:
        raise KeyError(f"Revenue fields missing in revenue data: {missing}")
    # ------------------------------------------------------------
    # 5. Convert from d,dd to float
    # ------------------------------------------------------------
    for c in rev_fields:
        rev_df[c] = (
            rev_df[c]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .replace({"nan": None, "None": None, "": None})
        )
        rev_df[c] = pd.to_numeric(rev_df[c], errors="coerce")
    # ------------------------------------------------------------
    # 6. Aggregate revenue data by join fields
    # ------------------------------------------------------------
    group_cols = list(join_fields.values())
    rev_grouped = (
        rev_df
        .groupby(group_cols)[rev_fields]
        .sum()
        .reset_index()
    )
    # ------------------------------------------------------------
    # 7. Compute revenue column using formula
    # ------------------------------------------------------------
    formula = rev_cfg.get("rev_formula", "AVG").upper()
    if formula == "AVG":
        rev_grouped["revenue"] = rev_grouped[rev_fields].mean(axis=1)
    elif formula == "SUM":
        rev_grouped["revenue"] = rev_grouped[rev_fields].sum(axis=1)
    elif formula == "MEDIAN":
        rev_grouped["revenue"] = rev_grouped[rev_fields].median(axis=1)
    elif formula == "MIN":
        rev_grouped["revenue"] = rev_grouped[rev_fields].min(axis=1)
    elif formula == "MAX":
        rev_grouped["revenue"] = rev_grouped[rev_fields].max(axis=1)
    else:
        raise ValueError(f"Invalid revenue formula '{formula}'.")
    # ------------------------------------------------------------
    # 8. Join with dataset
    # ------------------------------------------------------------
    merge_left = list(join_fields.keys())
    merge_right = list(join_fields.values())
    include_all = bool(rev_cfg.get("rev_include_all_addresses", True))
    how = "left" if include_all else "inner"
    df = df.merge(
        rev_grouped[group_cols + ["revenue"]],
        left_on=merge_left,
        right_on=merge_right,
        how=how,
    )
    # ------------------------------------------------------------
    # 9. Fill missing revenue if needed
    # ------------------------------------------------------------
    if include_all:
        df["revenue"] = df["revenue"].fillna(0.0)
    # ------------------------------------------------------------
    # 10. Cleanup
    # ------------------------------------------------------------
    df.drop(columns=group_cols, inplace=True, errors="ignore")
    df["revenue"] = df["revenue"].astype(float)
    return df

def resolve_lon_lat_columns(
    df: pd.DataFrame,
    col_map: Dict[str, Any],
) -> pd.DataFrame:
    """
    Resolve lon/lat columns in exactly one of two modes:

    DIRECT MODE:
        "lon": {"name": "..."}
        "lat": {"name": "..."}

    VECTOR MODE:
        "lon": {"name_from": "...", "name_to": "..."}
        "lat": {"name_from": "...", "name_to": "..."}
        "fraction": float (optional, default = 0.9)

    Always produces numeric lon/lat columns.
    Applies EPSG transform if "transform" is present in col_map.
    """

    # ------------------------------------------------------------
    # 0. Presence checks
    # ------------------------------------------------------------
    lon_cfg = col_map.get("lon")
    lat_cfg = col_map.get("lat")

    if lon_cfg is None or lat_cfg is None:
        raise KeyError("Both 'lon' and 'lat' must be defined in col_map.")

    direct_lon_same_name = lon_cfg.get("name") == "lon"
    direct_lat_same_name = lat_cfg.get("name") == "lat"
    if "lon" in df.columns and not direct_lon_same_name:
        df.rename(columns={"lon": "lon_orig"}, inplace=True)
    if "lat" in df.columns and not direct_lat_same_name:
        df.rename(columns={"lat": "lat_orig"}, inplace=True)
    # ------------------------------------------------------------
    # 1. Mode detection
    # ------------------------------------------------------------
    direct_mode = (
        "name" in lon_cfg and
        "name" in lat_cfg
    )
    vector_mode = (
        "name_from" in lon_cfg and "name_to" in lon_cfg and
        "name_from" in lat_cfg and "name_to" in lat_cfg
    )
    if direct_mode and vector_mode:
        raise ValueError(
            "Invalid lon/lat configuration: "
            "use either direct mode ('name') OR vector mode "
            "('name_from' + 'name_to'), not both."
        )
    if not direct_mode and not vector_mode:
        raise ValueError(
            "Invalid lon/lat configuration: "
            "expected either:\n"
            "  - lon/lat with 'name'\n"
            "  - lon/lat with 'name_from' and 'name_to'"
        )
    # ------------------------------------------------------------
    # 2. DIRECT MODE
    # ------------------------------------------------------------
    if direct_mode:
        lon_src = lon_cfg["name"]
        lat_src = lat_cfg["name"]
        missing = [c for c in (lon_src, lat_src) if c not in df.columns]
        if missing:
            raise KeyError(f"Lon/lat source columns missing in CSV: {missing}")
        df.rename(
            columns={
                lon_src: "lon",
                lat_src: "lat",
            },
            inplace=True,
        )
    # ------------------------------------------------------------
    # 3. VECTOR MODE
    # ------------------------------------------------------------
    else:
        lon_from = lon_cfg["name_from"]
        lon_to = lon_cfg["name_to"]
        lat_from = lat_cfg["name_from"]
        lat_to = lat_cfg["name_to"]
        missing = [
            c for c in (lon_from, lon_to, lat_from, lat_to)
            if c not in df.columns
        ]
        if missing:
            raise KeyError(
                f"Vector lon/lat columns missing in CSV: {missing}"
            )
        fraction = col_map.get("fraction", 0.9)
        if not isinstance(fraction, (int, float)):
            raise TypeError("'fraction' must be a number.")
        for col in (lon_from, lon_to, lat_from, lat_to):
            if df[col].dtype == object:
                df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = df[col].astype(float)
        df["lon"] = (df[lon_to] - df[lon_from]) * fraction + df[lon_from]
        df["lat"] = (df[lat_to] - df[lat_from]) * fraction + df[lat_from]
    # ------------------------------------------------------------
    # 4. Final cleanup (shared)
    # ------------------------------------------------------------
    for col in ("lon", "lat"):
        if df[col].dtype == object:
            df[col] = df[col].str.replace(",", ".", regex=False)
        df[col] = df[col].astype(float)
    # ------------------------------------------------------------
    # 5. EPSG transform (optional)
    # ------------------------------------------------------------
    if "transform" in col_map:
        tf = col_map["transform"]
        if "convert_from" not in tf or "convert_to" not in tf:
            raise KeyError(
                "'transform' must define 'convert_from' and 'convert_to'."
            )
        transformer = pyproj.Transformer.from_crs(
            tf["convert_from"],
            tf["convert_to"],
            always_xy=True,
        )
        lon_new, lat_new = [], []
        for x, y in zip(df["lon"], df["lat"]):
            lon, lat = transformer.transform(x, y)
            lon_new.append(lon)
            lat_new.append(lat)
        df["lon"] = lon_new
        df["lat"] = lat_new
    return df

def _apply_selector_filter(
    df: pd.DataFrame,
    selector: Optional[Dict[str, Any]],
) -> pd.DataFrame:
    if not selector:
        return df

    column = selector.get("column") or selector.get("name")
    if not column:
        raise ValueError("selector must define 'column' or 'name'.")
    if column not in df.columns:
        raise KeyError(f"Selector column '{column}' does not exist in dataset.")

    if "values" in selector:
        values = selector["values"]
    elif "value" in selector:
        values = [selector["value"]]
    else:
        raise ValueError("selector must define 'value' or 'values'.")

    if not isinstance(values, (list, tuple, set, pd.Index)):
        values = [values]

    filtered = df[df[column].isin(list(values))].copy()
    if filtered.empty:
        raise ValueError(
            f"Selector on '{column}' with values={list(values)} matched 0 rows."
        )
    return filtered

def prepare_dataset_for_runner(
    file_path: str,
    col_map: Dict[str, Dict[str, str]],
    file_seperator: str = ";",
    selector: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
    """
    Loads a CSV, applies simple renaming, optional EPSG coordinate transform,
    computes n_postboxes, preserves optional internal stop cost (L_u),
    derives distance_type / annotation_type / problem_type, and returns
    a clean dataset.

    Internal unified names: lon, lat, line_nr, route_id
    """
    DERIVED_COLUMNS = {
        "lon",
        "lat",
        "fraction",
        "type",
        "problem_type",
        "transform",
        "address",
        "revenue",
        "group_by_route_id",
    }
    # ------------------------------------------------------------
    # 1. Load CSV
    # ------------------------------------------------------------
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV data file does not exist: {file_path}")
    df = pd.read_csv(file_path, sep=file_seperator)
    # ------------------------------------------------------------
    # 2. Resolve conflicts if CSV already has the key name
    # ------------------------------------------------------------
    for internal_name, rule in col_map.items():
        if internal_name in DERIVED_COLUMNS:
            continue
        src_name = rule["name"]
        if internal_name in df.columns and internal_name != src_name:
            df.rename(columns={internal_name: f"{internal_name}_orig"}, inplace=True)

    # ------------------------------------------------------------
    # 3. Validate mapping keys exist in CSV
    # ------------------------------------------------------------
    for internal, rule in col_map.items():
        if internal in DERIVED_COLUMNS:
            continue
        src = rule["name"]
        if src not in df.columns:
            raise KeyError(f"Column '{src}' from col_map does not exist in CSV.")

    # ------------------------------------------------------------
    # 4. Apply renaming
    # ------------------------------------------------------------
    rename_dict = {
        rule["name"]: internal
        for internal, rule in col_map.items()
        if internal not in DERIVED_COLUMNS
    }
    df.rename(columns=rename_dict, inplace=True)

    # ------------------------------------------------------------
    # 4b. Optional selector-based filtering
    # ------------------------------------------------------------
    df = _apply_selector_filter(df, selector)

    # ------------------------------------------------------------
    # 5. Attach revenue data (optional, config-driven)
    # ------------------------------------------------------------
    df = attach_revenue_data(df, col_map)

    # ------------------------------------------------------------
    # 6. Resolve lon/lat (direct OR vector) + EPSG transform
    # ------------------------------------------------------------    
    df = resolve_lon_lat_columns(df, col_map)

    # ------------------------------------------------------------
    # 7. Ensure line_nr is numeric
    # ------------------------------------------------------------
    if "line_nr" not in df.columns:
        raise KeyError("You must map a column to 'line_nr' (formerly linienr).")
    df["line_nr"] = pd.to_numeric(df["line_nr"], errors="raise")

    group_by_route_id = bool(col_map.get("group_by_route_id", False))
    coord_group_cols = ["lon", "lat"]
    if group_by_route_id and "route_id" in df.columns:
        coord_group_cols = ["route_id", "lon", "lat"]

    # ------------------------------------------------------------
    # 8. Aggregate revenue per coordinate scope if present
    # ------------------------------------------------------------
    if "revenue" in df.columns:
        revenue_agg = (
            df.groupby(coord_group_cols, as_index=False)["revenue"]
            .sum()
        )

        df = df.drop(columns=["revenue"])
        df = df.merge(revenue_agg, on=coord_group_cols, how="left")

    # ------------------------------------------------------------
    # 9. Compute n_postboxes
    # ------------------------------------------------------------
    df_counts = (
        df.groupby(coord_group_cols)
        .size()
        .reset_index(name="n_postboxes")
    )
    df = df.merge(df_counts, on=coord_group_cols, how="left")

    # ------------------------------------------------------------
    # 10. Preserve optional internal stop cost per coordinate scope
    # ------------------------------------------------------------
    if "L_u" in df.columns:
        if df["L_u"].dtype == object:
            df["L_u"] = df["L_u"].str.replace(",", ".", regex=False)
        df["L_u"] = pd.to_numeric(df["L_u"], errors="raise")

        lu_agg = (
            df.groupby(coord_group_cols, as_index=False)["L_u"]
            .mean()
        )

        df = df.drop(columns=["L_u"])
        df = df.merge(lu_agg, on=coord_group_cols, how="left")

    # ------------------------------------------------------------
    # 11. Merge address fields per (lon, lat)
    # ------------------------------------------------------------
    if "address" in col_map:
        addr_cfg = col_map["address"]
        fields: List[str] = addr_cfg.get("fields", [])
        sep: str = addr_cfg.get("separator", "; ")
        missing = [f for f in fields if f not in df.columns]
        if missing:
            raise KeyError(f"Address fields missing in CSV: {missing}")

        df["_address_raw"] = (
            df[fields]
            .astype(str)
            .apply(
                lambda r: sep.join(v for v in r if v and v.lower() != "nan"),
                axis=1
            )
        )

        addr_agg = (
            df.groupby(coord_group_cols)["_address_raw"]
            .apply(lambda x: sep.join(sorted(set(x))))
            .reset_index(name="address")
        )

        df = df.merge(addr_agg, on=coord_group_cols, how="left")
        df.drop(columns=["_address_raw"], inplace=True)

    # ------------------------------------------------------------
    # 12. Derive distance_type and annotation_type from col_map["type"]
    # ------------------------------------------------------------
    if "type" in col_map:
        type_cfg = col_map["type"]
        src_col = type_cfg.get("name")

        if src_col not in df.columns:
            raise KeyError(f"Type source column '{src_col}' does not exist in CSV.")

        value_lookup = {}
        for dist_type, cfg in type_cfg.items():
            if dist_type == "name":
                continue
            value_lookup[cfg["val"]] = (dist_type, cfg["annotations"])

        def _resolve_type(val):
            if val in value_lookup:
                return value_lookup[val]
            return ("foot", "distance")

        resolved = df[src_col].apply(_resolve_type)
        df["distance_type"] = resolved.apply(lambda x: x[0])
        df["annotation_type"] = resolved.apply(lambda x: x[1])
    else:
        df["distance_type"] = "foot"
        df["annotation_type"] = "distance"

    # ------------------------------------------------------------
    # 13. Derive problem_type (HPP / TSP)
    # ------------------------------------------------------------
    if "problem_type" in col_map:
        pt_cfg = col_map["problem_type"]
        src_col = pt_cfg.get("name")
        src_values = df[src_col].copy() if src_col in df.columns else None

        if src_col in df.columns:
            hpp_vals = set(pt_cfg.get("HPP", []))
            out_hpp_vals = set(pt_cfg.get("OUT:HPP", []))
            tsp_vals = set(pt_cfg.get("TSP", []))
            out_tsp_vals = set(pt_cfg.get("OUT:TSP", []))

            def _resolve_problem_type(val):
                if val in hpp_vals:
                    return "HPP"
                if val in out_hpp_vals:
                    return "OUT:HPP"
                if val in tsp_vals:
                    return "TSP"
                if val in out_tsp_vals:
                    return "OUT:TSP"
                return "TSP"

            df["problem_type"] = src_values.apply(_resolve_problem_type)
        else:
            df["problem_type"] = "TSP"
    else:
        df["problem_type"] = "TSP"

    return df

def resolve_route_apr_profile(
    data: pd.DataFrame,
    APR: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
    """
    Resolve routing metadata for a single route.
    Returns:
        {
            "profile": str,
            "annotation": str,
            "APR": float,
            "unit": str,
        }
    """
    profiles = data["distance_type"].unique()
    if len(profiles) != 1:
        raise ValueError(
            f"Multiple distance_type values found in route: {profiles}"
        )
    profile = profiles[0]
    annotations = data["annotation_type"].unique()
    if len(annotations) != 1:
        raise ValueError(
            f"Multiple annotation_type values found in route: {annotations}"
        )
    annotation = annotations[0]
    VALID_PROFILES = {"foot", "car", "car-newyork", "bike", "bicycle"}
    VALID_ANNOTATIONS = {"distance", "duration"}
    if profile not in VALID_PROFILES:
        raise ValueError(
            f"Invalid profile '{profile}'. "
            f"Expected one of {sorted(VALID_PROFILES)}"
        )
    if annotation not in VALID_ANNOTATIONS:
        raise ValueError(
            f"Invalid annotation '{annotation}'. "
            f"Expected one of {sorted(VALID_ANNOTATIONS)}"
        )
    try:
        apr_value = APR[profile][annotation]
    except KeyError:
        raise KeyError(
            f"No APR defined for profile='{profile}', annotation='{annotation}'."
        )
    unit = "m" if annotation == "distance" else "sec"
    return {
        "profile": profile,
        "annotation": annotation,
        "APR": apr_value,
        "unit": unit,
    }

def resolve_problem_type(data: pd.DataFrame) -> PROBLEM_TYPES:
    """
    Resolve problem_type for a single route.

    Returns:
        "HPP" or "TSP"

    Raises:
        ValueError if problem_type is missing or not unique.
    """
    if "problem_type" not in data.columns:
        raise KeyError("Column 'problem_type' does not exist in dataset.")
    problem_types = data["problem_type"].unique()
    if len(problem_types) != 1:
        raise ValueError(
            f"Multiple problem_type values found in route: {problem_types}"
        )
    problem_type = problem_types[0]
    if problem_type not in PROBLEM_TYPES_SET:
        raise ValueError(
            f"Invalid problem_type '{problem_type}'. "
            "Expected one of ['HPP', 'TSP']"
        )
    return problem_type

def _unit_entry_exit_first_last_address(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Entry = first address in unit (by route_nr)
    Exit  = last  address in unit (by route_nr)
    """
    for _, g in df.groupby("unit_number", sort=False):
        g_sorted = g.sort_values("route_nr")
        entry = g_sorted.iloc[0]
        exit_ = g_sorted.iloc[-1]
        df.loc[g.index, "unit_start_point_lon"] = entry["lon"]
        df.loc[g.index, "unit_start_point_lat"] = entry["lat"]
        df.loc[g.index, "unit_end_point_lon"] = exit_["lon"]
        df.loc[g.index, "unit_end_point_lat"] = exit_["lat"]
    return df

def _unit_entry_exit_osrm_closest(
    df: pd.DataFrame,
    *,
    profile: str,
) -> pd.DataFrame:
    """
    Entry = address closest (OSRM distance) to snapped unit start
    Exit  = address closest (OSRM distance) to snapped unit end
    """
    client = OSRMClient(profile=profile)

    def _argmin_ignore_none(values: list[float | None]) -> int:
        valid = [(i, v) for i, v in enumerate(values) if v is not None]
        if not valid:
            raise RuntimeError(
                "OSRM returned no valid distances (all None). "
                "Check geometry, profile, or connectivity."
            )
        return min(valid, key=lambda x: x[1])[0]
    
    for _, g in df.groupby("unit_number", sort=False):
        g = g.sort_values("route_nr")
        addresses = g[["lon", "lat"]].to_dict("records")

        start = {
            "lon": float(g.iloc[0]["unit_start_point_lon"]),
            "lat": float(g.iloc[0]["unit_start_point_lat"]),
        }
        end = {
            "lon": float(g.iloc[0]["unit_end_point_lon"]),
            "lat": float(g.iloc[0]["unit_end_point_lat"]),
        }
        # ---- start → addresses ----
        locs = [start] + addresses
        res = client.table(
            locs,
            sources=[0],
            destinations=list(range(1, len(locs))),
            annotations="distance",
        )
        d_start = res["distances"][0]
        i_start = _argmin_ignore_none(d_start)
        entry = addresses[i_start]
        # ---- addresses → end ----
        locs = addresses + [end]
        res = client.table(
            locs,
            sources=list(range(len(addresses))),
            destinations=[len(locs) - 1],
            annotations="distance",
        )
        d_end = [row[0] for row in res["distances"]]
        i_end = _argmin_ignore_none(d_end)
        exit_ = addresses[i_end]
        df.loc[g.index, "unit_start_point_lon"] = entry["lon"]
        df.loc[g.index, "unit_start_point_lat"] = entry["lat"]
        df.loc[g.index, "unit_end_point_lon"] = exit_["lon"]
        df.loc[g.index, "unit_end_point_lat"] = exit_["lat"]
    return df

def _apply_unit_entry_exit_strategy(
    df: pd.DataFrame,
    *,
    strategy: str | None,
    osrm_profile: str,
) -> pd.DataFrame:
    if strategy is None or strategy == "SNAPPED":
        return df
    if strategy == "FIRST_LAST_ADDRESS":
        return _unit_entry_exit_first_last_address(df)
    if strategy == "OSRM_CLOSEST":
        return _unit_entry_exit_osrm_closest(df, profile=osrm_profile)
    raise ValueError(
        f"Invalid unit_entry_exit_strategy '{strategy}'. "
        "Expected one of: None, 'snapped', 'first_last_address', 'osrm_closest'."
    )

def prepare_route(  route_id: str,
                    df: pd.DataFrame,
                    APR: Dict[str, Dict[str, float]],
                    allowed_highways: List[str] | None = None,
                    chunk_size: int | None = None,
                    use_rotated_side: bool = False,
                    offset_m: float = 4.5,
                    entry_angle_deg: float = -60.0,
                    exit_angle_deg: float = 60.0,
                    unit_entry_exit_strategy: str | None = None,
                  ) -> Dict[str, Any]:
    # --------------------------------------------------
    # 1. Filter + deduplicate route
    # --------------------------------------------------
    data = df[df["route_id"] == route_id].copy()
    unique_sorted = (
            data.sort_values("line_nr")
            .drop_duplicates(subset=["lon", "lat"])
            .reset_index(drop=True)
        )
    unique_sorted["route_nr"] = range(len(unique_sorted))
    # --------------------------------------------------
    # 2. Resolve APR + problem type
    # --------------------------------------------------
    APR_profile = resolve_route_apr_profile(
                    data = unique_sorted,
                    APR = APR
                    )
    problem_type = resolve_problem_type(data=data)
    # --------------------------------------------------
    # 3. Structured routing → snap + unit assignment
    # --------------------------------------------------
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        points = unique_sorted[["lon", "lat"]].to_dict(orient="records")
        unit_rows = snap_points_with_units(
            points = points,
            show_progress=True,
            allowed_highways=allowed_highways,
            x_key="lon",
            y_key="lat",
            chunk_size=chunk_size,
            use_rotated_side=use_rotated_side,
            offset_m = offset_m,
            entry_angle_deg = entry_angle_deg,
            exit_angle_deg = exit_angle_deg,
        )
        if len(unit_rows) != len(unique_sorted):
            raise RuntimeError(
                "snap_points_with_units returned mismatched number of rows"
            )
        # --------------------------------------------------
        # 4. Write returned fields as columns
        # --------------------------------------------------
        for col in [
            "segment_id",
            "side_of_road",
            "unit_number",
            "unit_start_point_lon",
            "unit_start_point_lat",
            "unit_end_point_lon",
            "unit_end_point_lat",
        ]:
            unique_sorted[col] = [row[col] for row in unit_rows]
        
        # --------------------------------------------------
        # 4b. Apply unit entry/exit strategy 
        # --------------------------------------------------
        unique_sorted = _apply_unit_entry_exit_strategy(
            unique_sorted,
            strategy=unit_entry_exit_strategy,
            osrm_profile=APR_profile["profile"],
        )
    # --------------------------------------------------
    # 5. Return result
    # --------------------------------------------------
    return {
        "data": unique_sorted,
        "APR_profile": APR_profile,
        "problem_type": problem_type,
    }

