import numpy as np
import pandas as pd

from libraries.utils.pipelines.b_route_preparation_layer import pipeline_prepare_route as mod


def test_prepare_route_and_matrices_reads_constant_L_u(monkeypatch):
    source_df = pd.DataFrame(
        {
            "route_id": ["r1", "r1"],
            "line_nr": [1, 2],
            "lon": [12.0, 13.0],
            "lat": [55.0, 56.0],
            "L_u": [30.0, 30.0],
            "distance_type": ["car-newyork", "car-newyork"],
            "annotation_type": ["duration", "duration"],
            "problem_type": ["HPP", "HPP"],
        }
    )

    def fake_prepare_route(**kwargs):
        return {
            "data": source_df.copy(),
            "APR_profile": {
                "profile": "car-newyork",
                "annotation": "duration",
                "APR": 0.03944,
                "unit": "sec",
            },
            "problem_type": "HPP",
        }

    def fake_prepare_route_data(**kwargs):
        return {
            "data": kwargs["data"],
            "Distance_Matrix": np.array([[0.0, 1.0], [1.0, 0.0]]),
            "p": np.array([1, 1]),
            "R": [0, 1],
            "nodes": None,
        }

    monkeypatch.setattr(mod, "prepare_route", fake_prepare_route)
    monkeypatch.setattr(mod, "prepare_route_data", fake_prepare_route_data)

    route_prep = mod.prepare_route_and_matrices(
        route_id="r1",
        df=source_df,
        APR={"car-newyork": {"duration": 0.03944}},
        solver_tsp="ortools",
        solver_hpp="ortools",
        deterministic_tsp=True,
        deterministic_hpp=True,
    )

    assert route_prep.L_u == 30.0
