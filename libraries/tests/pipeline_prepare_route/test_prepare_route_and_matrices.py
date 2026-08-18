import copy
import pprint

from libraries.utils.pipelines.a_context_layer.pipeline_dataset_context import (
    init_pipeline_context,
)
from libraries.utils.pipelines.b_route_preparation_layer.pipeline_prepare_route import (
    prepare_route_and_matrices,
    RoutePrep,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


# ---------------------------------------------------------------------
# Base configuration (shared across all tests)
# ---------------------------------------------------------------------
BASE_CONFIG = {
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
    },
    "route_type": "both",
    "APR": 0.03,
    "start_routes": None,
    "max_routes": None,
    "solver_tsp": "ortools",
    "solver_hpp": "ortools",
    "deterministic_tsp": True,
    "deterministic_hpp": True,
}


# ---------------------------------------------------------------------
# Problem type variants (ONLY difference between tests)
# ---------------------------------------------------------------------
PROBLEM_TYPE_VARIANTS = {
    "TSP/HPP": {
        "name": "beregning",
        "HPP": [1],
        "TSP": [0, 2],
    },
    "OUT:TSP/OUT:HPP": {
        "name": "beregning",
        "OUT:HPP": [1],
        "OUT:TSP": [0, 2],
    },
}


def _run_prepare_route_test(problem_type_mapping: dict):
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSRM service not running",
    )

    # --------------------------------------------------
    # Inject problem_type mapping into config
    # --------------------------------------------------
    config = copy.deepcopy(BASE_CONFIG)
    config["col_map"]["problem_type"] = problem_type_mapping

    # --------------------------------------------------
    # Step 1: build pipeline context
    # --------------------------------------------------
    ctx = init_pipeline_context(
        file_path=config["dataset"],
        col_map=config["col_map"],
        route_type=config["route_type"],
        A_kwargs=None,
        B_kwargs=None,
        U_kwargs=None,
        APR=config["APR"],
        start_routes=config["start_routes"],
        max_routes=config["max_routes"],
    )

    assert len(ctx.route_ids) > 0
    route_id = ctx.route_ids[0]

    # --------------------------------------------------
    # Step 2: prepare route + matrices
    # --------------------------------------------------
    route_prep = prepare_route_and_matrices(
        route_id=route_id,
        df=ctx.df,
        APR=ctx.APR,
        solver_tsp=config["solver_tsp"],
        solver_hpp=config["solver_hpp"],
        deterministic_tsp=config["deterministic_tsp"],
        deterministic_hpp=config["deterministic_hpp"],
        chunk_size_osrm= 50,
        chunk_size_osm = 2,
        use_rotated_side = True,
        offset_m = 4.5,
        entry_angle_deg = 60.0,
        exit_angle_deg = 60.0,
    )

    # --------------------------------------------------
    # Assertions: structure
    # --------------------------------------------------
    assert isinstance(route_prep, RoutePrep)
    assert route_prep.route_id == route_id
    assert isinstance(route_prep.data, dict)
    assert isinstance(route_prep.APR_profile, dict)
    assert isinstance(route_prep.problem_type, str)
    assert isinstance(route_prep.solver, str)
    assert isinstance(route_prep.deterministic, bool)
    assert isinstance(route_prep.L_u, float)

    # --------------------------------------------------
    # Assertions: solver selection
    # --------------------------------------------------
    if route_prep.problem_type in {"TSP", "OUT:TSP"}:
        assert route_prep.solver == config["solver_tsp"]
        assert route_prep.deterministic == config["deterministic_tsp"]
    else:
        assert route_prep.solver == config["solver_hpp"]
        assert route_prep.deterministic == config["deterministic_hpp"]

    # --------------------------------------------------
    # Assertions: distance matrix & core fields
    # --------------------------------------------------
    data = route_prep.data
    print(data)
    assert "Distance_Matrix" in data
    assert "p" in data
    assert "R" in data
    assert len(data["p"]) == len(data["R"])
    if route_prep.problem_type in {"OUT:HPP", "OUT:TSP"}:
        assert data.get("nodes") is not None
    else:
        assert data.get("nodes") is None

    # --------------------------------------------------
    # PRINTS (intentional)
    # --------------------------------------------------
    print("\n[TEST] prepare_route_and_matrices")
    print("-" * 70)
    print(f"Problem type mapping : {problem_type_mapping}")
    print(f"Route ID             : {route_prep.route_id}")
    print(f"Resolved problem type: {route_prep.problem_type}")
    print(f"Solver               : {route_prep.solver}")
    print(f"Deterministic        : {route_prep.deterministic}")
    print("\nAPR_profile:")
    pprint.pprint(route_prep.APR_profile)
    print("-" * 70)


# ---------------------------------------------------------------------
# Actual tests
# ---------------------------------------------------------------------
def test_prepare_route_and_matrices_tsp_hpp():
    _run_prepare_route_test(PROBLEM_TYPE_VARIANTS["TSP/HPP"])


def test_prepare_route_and_matrices_out_tsp_out_hpp():
    _run_prepare_route_test(PROBLEM_TYPE_VARIANTS["OUT:TSP/OUT:HPP"])


if __name__ == "__main__":
    test_prepare_route_and_matrices_tsp_hpp()
    test_prepare_route_and_matrices_out_tsp_out_hpp()
