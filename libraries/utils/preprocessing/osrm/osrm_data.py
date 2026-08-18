import numpy as np
import pandas as pd
from typing import Dict, Any, Literal, List, Dict, Tuple
from libraries.classes.osrm_api import OSRMClient
from libraries.config import STRUCTURED_PROBLEM_TYPES, STRUCTURED_PROBLEM_TYPES_SET

def extract_structured_nodes_and_coords(
    df: pd.DataFrame,
) -> Tuple[
    List[Tuple[float, float]],   # coordinates (lon, lat)
    List[Dict],                  # nodes
]:
    """
    Convert a structured route dataframe into:
      1) a coordinate list for D_full
      2) a node list compatible with build_structured_route_data

    Ordering per unit:
      [unit_start] -> addresses (in route order) -> [unit_end]
    """

    locations: List[Dict[str, float]] = []
    nodes: List[Dict] = []

    m_index = 0  # global index into D_full

    # --------------------------------------------------
    # Process units in ascending unit_number
    # --------------------------------------------------
    for unit_id, unit_df in df.groupby("unit_number", sort=True):

        unit_df = unit_df.sort_values("route_nr")

        # -----------------------------
        # Unit start node
        # -----------------------------
        start_lon = unit_df.iloc[0]["unit_start_point_lon"]
        start_lat = unit_df.iloc[0]["unit_start_point_lat"]

        locations.append({"lon": float(start_lon), "lat": float(start_lat)})
        nodes.append(
            {
                "m_index": m_index,
                "unit": int(unit_id),
                "type": "start",
                "route_number": None,
            }
        )
        m_index += 1

        # -----------------------------
        # Address nodes
        # -----------------------------
        for _, row in unit_df.iterrows():
            locations.append({"lon": float(row["lon"]), "lat":float(row["lat"])})
            nodes.append(
                {
                    "m_index": m_index,
                    "unit": int(unit_id),
                    "type": "address",
                    "route_number": int(row["route_nr"]),
                }
            )
            m_index += 1

        # -----------------------------
        # Unit end node
        # -----------------------------
        end_lon = unit_df.iloc[0]["unit_end_point_lon"]
        end_lat = unit_df.iloc[0]["unit_end_point_lat"]

        locations.append({"lon": float(end_lon), "lat": float(end_lat)})
        nodes.append(
            {
                "m_index": m_index,
                "unit": int(unit_id),
                "type": "end",
                "route_number": None,
            }
        )
        m_index += 1
    return locations, nodes


def prepare_route_data(
    data: pd.DataFrame,
    problem_type: STRUCTURED_PROBLEM_TYPES,
    chunk_size: int = 50,
    profile: Literal["foot", "car", "bike", "bicycle"] = "foot",
    annotation: Literal["distance", "duration"] = "distance",
    ) -> Dict[str, Any]:
    """
    Prepares all route-specific input data used by the OSRM layer and the
    outlier algorithms (Type 1 and Type 2).
    -----------------------------------------------------------------------
    Parameters:
    data : Route data containing lon/lat, n_postboxes, route_nr.
    chunk_size : Number of OSRM-table subrequests.
    profile : OSRM routing profile (local mode selects correct OSRM instance).

    annotation : OSRM table annotation to compute.
    -----------------------------------------------------------------------
    Returns:
        {
            "data"            : pd.DataFrame,
            "Distance_Matrix" : np.ndarray,
            "p"               : np.ndarray,
            "R"               : List[int],
        }
    """
    client = OSRMClient(profile=profile)
    if problem_type in STRUCTURED_PROBLEM_TYPES_SET:
        locations, nodes = extract_structured_nodes_and_coords(data)
    else:
        locations = data[["lon", "lat"]].to_dict("records")
        nodes = None

    D = np.array(
        client.table_chunked(
            locations,
            chunk_size=chunk_size,
            annotations=annotation,
            profile=profile,
        )
    )
    p = np.array(data["n_postboxes"])
    R = [int(x) for x in data["route_nr"]]
    return {
        "data": data,
        "Distance_Matrix": D,
        "p": p,
        "R": R,
        "nodes": nodes,
    }

