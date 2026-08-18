from pathlib import Path

from libraries.utils.runtime.runtime_loader import load_runtime_context
from libraries.utils.pipelines.pipelines.application.v1.run_route_data_pipeline import (
    run_route_data_pipeline,
)


def run_data_from_runtime(runtime_dir: str):
    """
    Execute the single-scenario demo application data pipeline
    using a runtime definition directory.
    """

    ctx = load_runtime_context(Path(runtime_dir))
    config = ctx["config"]
    mappings_cfg = config.get("mappings", {})
    input_cfg = config.get("input", {})
    output_cfg = config.get("output", {})
    routing_cfg = config.get("routing", {})
    algo_cfg = config.get("algorithm", {})
    geom_cfg = config.get("geometry", {})
    flags_cfg = config.get("flags", {})

    return run_route_data_pipeline(
        file_path=input_cfg["file_path"],
        file_seperator=input_cfg.get("file_seperator", ";"),
        save_dir=output_cfg.get(
            "save_dir",
            "./views/application/demo_bus_routes_nyc_single_scenario/data",
        ),
        route_type=routing_cfg.get("route_type", "both"),
        start_routes=routing_cfg.get("start_routes"),
        max_routes=routing_cfg.get("max_routes"),
        E=algo_cfg.get("E", 5.0),
        APR=algo_cfg.get("APR", 0.03),
        z=algo_cfg.get("z", 0.0),
        k_max=algo_cfg.get("k_max", 25),
        k_all=algo_cfg.get("k_all", 1),
        B=algo_cfg.get("B", 10),
        solver_tsp=algo_cfg.get("solver_tsp", "ortools"),
        solver_hpp=algo_cfg.get("solver_hpp", "ortools"),
        deterministic_tsp=algo_cfg.get("deterministic_tsp", True),
        deterministic_hpp=algo_cfg.get("deterministic_hpp", True),
        precheck=algo_cfg.get("precheck", True),
        type1_methods=algo_cfg.get("type1_methods"),
        type2_methods=algo_cfg.get("type2_methods"),
        ortools_time_limit=algo_cfg.get("ortools_time_limit", 5),
        initial_point_method=algo_cfg.get("initial_point_method"),
        A_kwargs=algo_cfg.get("A_kwargs"),
        B_kwargs=algo_cfg.get("B_kwargs"),
        U_kwargs=algo_cfg.get("U_kwargs"),
        allowed_highways=geom_cfg.get("allowed_highways"),
        chunk_size_osm=geom_cfg.get("chunk_size_osm"),
        chunk_size_osrm=geom_cfg.get("chunk_size_osrm", 50),
        use_rotated_side=geom_cfg.get("use_rotated_side", True),
        offset_m=geom_cfg.get("offset_m", 4.5),
        entry_angle_deg=geom_cfg.get("entry_angle_deg", 60.0),
        exit_angle_deg=geom_cfg.get("exit_angle_deg", 60.0),
        unit_entry_exit_strategy=geom_cfg.get("unit_entry_exit_strategy"),
        col_map=mappings_cfg.get("col_map"),
        kpi_mapping=mappings_cfg.get("kpi_mapping"),
        use_data=flags_cfg.get("use_data", False),
        index_filename=flags_cfg.get("index_filename", "routes_index.json"),
    )


if __name__ == "__main__":
    runtime_path = "./runtime_definitions/application/demo_bus_routes_nyc_single_scenario"
    run_data_from_runtime(runtime_path)
