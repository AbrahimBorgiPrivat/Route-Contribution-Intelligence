from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from libraries.utils.preprocessing.route_data_preparer import prepare_dataset_for_runner

@dataclass(frozen=True)
class PipelineContext:
    t0: float
    df: pd.DataFrame
    strict_values: List[bool]
    A_kwargs: Dict[str, Any]
    B_kwargs: Dict[str, Any]
    U_kwargs: Dict[str, Any]
    APR: Dict[str, Any]
    route_ids: List[Any]


def init_pipeline_context(
    *,
    file_path: str,
    col_map: Dict[str, Dict[str, str]],
    route_type: str,
    A_kwargs: Optional[Dict[str, Any]],
    B_kwargs: Optional[Dict[str, Any]],
    U_kwargs: Optional[Dict[str, Any]],
    APR: Union[int, float, Dict[str, Any]],
    start_routes: Optional[int] = None,
    max_routes: Optional[int] = None,
    selector: Optional[Dict[str, Any]] = None,
    file_seperator: str = ";"
) -> PipelineContext:
    t0 = time.perf_counter()
    df = prepare_dataset_for_runner(file_path=file_path, 
                                    col_map=col_map,
                                    file_seperator=file_seperator,
                                    selector=selector)
    if route_type == "type1":
        strict_values = [True]
    elif route_type == "type2":
        strict_values = [False]
    else:
        strict_values = [True, False]
    if A_kwargs is None:
        A_kwargs = {"method": "kneedle"}
    if B_kwargs is None:
        B_kwargs = {"L_max": 8}
    if U_kwargs is None:
        U_kwargs = {}
    if isinstance(APR, (int, float)):
        APR = {
            "foot": {"distance": float(APR), "duration": float(APR)},
            "bike": {"distance": float(APR), "duration": float(APR)},
            "bicycle": {"distance": float(APR), "duration": float(APR)},
            "car": {"distance": float(APR), "duration": float(APR)},
            "car-newyork": {"distance": float(APR), "duration": float(APR)},
        }
    route_ids = list(df["route_id"].unique())
    start = start_routes if start_routes is not None else 0
    end = None if max_routes is None else start + max_routes
    route_ids = route_ids[start:end]

    return PipelineContext(
        t0=t0,
        df=df,
        strict_values=strict_values,
        A_kwargs=A_kwargs,
        B_kwargs=B_kwargs,
        U_kwargs=U_kwargs,
        APR=APR,
        route_ids=route_ids,
    )
