import pprint
import os
import tempfile

import pandas as pd
import pytest

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
    PipelineContext,
)


def _write_temp_csv(df: pd.DataFrame) -> str:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="test_ctx_")
    os.close(tmp_fd)
    df.to_csv(tmp_path, sep=";", index=False)
    return tmp_path


CONFIG = {
    "dataset": "libraries/tests/_test_dataset/test_data.csv",
    "col_map": {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
        "address": {
            "fields": ["adresse"],
            "separator": "; ",
        },
        "transform": {
            "convert_from": "EPSG:25832",
            "convert_to": "EPSG:4326",
        },
        "type": {
            "name": "beregning",
            "foot": {"val": 0, "annotations": "distance"},
            "car": {"val": 1, "annotations": "duration"},
            "cycle": {"val": 2, "annotations": "distance"},
        },
        "problem_type": {
            "name": "beregning",
            "HPP": [1],
            "TSP": [0, 2],
        },
    },
    "route_type": "both",
    "APR": 0.03,  
    "A_kwargs": None,
    "B_kwargs": None,
    "U_kwargs": None,
    "start_routes": None,
    "max_routes": None,
}


def test_init_pipeline_context_basic():
    ctx = init_pipeline_context(
        file_path=CONFIG["dataset"],
        col_map=CONFIG["col_map"],
        route_type=CONFIG["route_type"],
        A_kwargs=CONFIG["A_kwargs"],
        B_kwargs=CONFIG["B_kwargs"],
        U_kwargs=CONFIG["U_kwargs"],
        APR=CONFIG["APR"],
        start_routes=CONFIG["start_routes"],
        max_routes=CONFIG["max_routes"],
    )

    # --------------------------------------------------
    # Assertions: structure
    # --------------------------------------------------
    assert isinstance(ctx, PipelineContext)

    assert isinstance(ctx.df, pd.DataFrame)
    assert not ctx.df.empty

    assert isinstance(ctx.route_ids, list)
    assert len(ctx.route_ids) > 0

    assert isinstance(ctx.strict_values, list)
    assert ctx.strict_values == [True, False]

    assert isinstance(ctx.A_kwargs, dict)
    assert isinstance(ctx.B_kwargs, dict)
    assert isinstance(ctx.APR, dict)

    # --------------------------------------------------
    # Assertions: APR normalization
    # --------------------------------------------------
    for mode in ["foot", "bike", "bicycle", "car"]:
        assert mode in ctx.APR
        assert (
            "distance" in ctx.APR[mode]
            or "duration" in ctx.APR[mode]
        )

    # --------------------------------------------------
    # PRINTS (intentional, for inspection)
    # --------------------------------------------------
    print("\n[TEST] init_pipeline_context (pure)")
    print("-" * 70)
    print(f"t0              : {ctx.t0:.6f}")
    print(f"Rows in dataset : {len(ctx.df)}")
    print(f"Route IDs ({len(ctx.route_ids)}): {ctx.route_ids}")
    print(f"Strict values   : {ctx.strict_values}")
    print(f"Data head: {ctx.df.head()}")

    print("\nA_kwargs:")
    pprint.pprint(ctx.A_kwargs)

    print("\nB_kwargs:")
    pprint.pprint(ctx.B_kwargs)

    print("\nAPR:")
    pprint.pprint(ctx.APR)

    print("-" * 70)


def test_init_pipeline_context_selector_filters_routes():
    df_raw = pd.DataFrame(
        {
            "id": ["A", "A", "B"],
            "route_group": ["Day Busses", "Night", "Day Busses"],
            "vejx": ["14,71", "14,72", "14,73"],
            "vejy": ["55,12", "55,13", "55,14"],
            "linienr": [0, 1, 2],
            "beregning": [0, 0, 0],
        }
    )
    csv_path = _write_temp_csv(df_raw)
    col_map = {
        "route_id": {"name": "id"},
        "lon": {"name": "vejx"},
        "lat": {"name": "vejy"},
        "line_nr": {"name": "linienr"},
    }

    ctx = init_pipeline_context(
        file_path=csv_path,
        col_map=col_map,
        route_type="both",
        A_kwargs=None,
        B_kwargs=None,
        U_kwargs=None,
        APR=0.03,
        start_routes=None,
        max_routes=None,
        selector={
            "column": "route_group",
            "values": ["Day Busses"],
        },
    )

    assert ctx.route_ids == ["A", "B"]
    assert set(ctx.df["route_group"]) == {"Day Busses"}

    os.remove(csv_path)


if __name__ == "__main__":
    test_init_pipeline_context_basic()
