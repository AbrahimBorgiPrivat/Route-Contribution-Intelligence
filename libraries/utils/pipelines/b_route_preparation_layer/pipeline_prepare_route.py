from typing import Dict, Any, List
from dataclasses import dataclass

import pandas as pd
import numpy as np

from libraries.utils.preprocessing.route_data_preparer import prepare_route
from libraries.utils.preprocessing.osrm.osrm_data import prepare_route_data


@dataclass(frozen=True)
class RoutePrep:
    """
    Immutable container holding all per-route information
    required by downstream pipeline stages.
    """
    route_id: Any
    data: Dict[str, Any]
    APR_profile: Dict[str, Any]
    problem_type: str
    solver: str
    deterministic: bool
    L_u: float


def prepare_route_and_matrices(
    *,
    route_id: Any,
    df: pd.DataFrame,
    APR: Dict[str, Any],
    solver_tsp: str,
    solver_hpp: str,
    deterministic_tsp: bool,
    deterministic_hpp: bool,
    chunk_size_osrm: int = 50,
    allowed_highways: List[str] | None = None,
    chunk_size_osm: int | None = None,
    use_rotated_side: bool = False,
    offset_m: float = 4.5,
    entry_angle_deg: float = 60.0,
    exit_angle_deg: float = 60.0,
    unit_entry_exit_strategy: str | None = None,
) -> RoutePrep:
    """
    Prepare a single route for optimization:
      1. Extract route-specific data
      2. Determine problem type (OUT:TSP / OUT:HPP / TSP / HPP)
      3. Select solver and determinism flags
      4. Build distance matrices via OSRM

    This function is pure:
      - no filesystem access
      - no global state
      - no algorithm execution
    """

    # --------------------------------------------------
    # Step 1: Extract route-specific data
    # --------------------------------------------------
    route_data = prepare_route(
        route_id=route_id,
        df=df,
        APR=APR,
        allowed_highways=allowed_highways,
        chunk_size=chunk_size_osm,
        use_rotated_side=use_rotated_side,
        offset_m=offset_m,
        entry_angle_deg=entry_angle_deg,
        exit_angle_deg=exit_angle_deg,
        unit_entry_exit_strategy=unit_entry_exit_strategy,
    )
    
    data = route_data["data"]
    APR_profile = route_data["APR_profile"]
    problem_type = route_data["problem_type"]
    L_u = 0.0
    if "L_u" in data.columns:
        lu_values = pd.to_numeric(data["L_u"], errors="raise").dropna().to_numpy(dtype=float)
        if lu_values.size > 0:
            if not np.allclose(lu_values, lu_values[0]):
                raise ValueError(
                    "Current application pipeline expects route-constant L_u values "
                    f"within each route. Route '{route_id}' has multiple values: "
                    f"{sorted(set(np.round(lu_values, 6)))}"
                )
            L_u = float(lu_values[0])

    # --------------------------------------------------
    # Step 2: Select solver based on problem type
    # --------------------------------------------------
    if problem_type == "TSP":
        solver = solver_tsp
        deterministic = deterministic_tsp
    else:
        solver = solver_hpp
        deterministic = deterministic_hpp

    # --------------------------------------------------
    # Step 3: Build distance matrices
    # --------------------------------------------------
    data = prepare_route_data(
        data=data,
        problem_type=problem_type,
        chunk_size=chunk_size_osrm,
        profile=APR_profile["profile"],
        annotation=APR_profile["annotation"],
    )

    # --------------------------------------------------
    # Step 4: Return immutable route context
    # --------------------------------------------------
    return RoutePrep(
        route_id=route_id,
        data=data,
        APR_profile=APR_profile,
        problem_type=problem_type,
        solver=solver,
        deterministic=deterministic,
        L_u=L_u,
    )
