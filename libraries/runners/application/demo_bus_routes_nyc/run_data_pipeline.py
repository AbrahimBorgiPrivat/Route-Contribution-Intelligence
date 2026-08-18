from pathlib import Path

from libraries.utils.runtime.runtime_loader import load_runtime_context
from libraries.utils.pipelines.pipelines.application.v2.run_route_data_pipeline import (
    run_route_data_pipeline_v2,
)


def run_data_from_runtime(runtime_dir: str):
    """
    Execute the demo_bus_routes_nyc multi-scenario application pipeline
    using a runtime definition directory.
    """

    ctx = load_runtime_context(Path(runtime_dir))
    config = ctx["config"]

    default_runner = config.get("default_runner", {})
    label_list = config.get("label_list", [])
    APR_profiles = config.get("APR_profiles", [])
    revenue_list = config.get("revenue_list", [])

    input_cfg = default_runner.get("input", {})
    routing_cfg = default_runner.get("routing", {})
    algo_cfg = default_runner.get("algorithm", {})
    geom_cfg = default_runner.get("geometry", {})
    mappings_cfg = default_runner.get("mappings", {})
    output_cfg = default_runner.get("output", {})
    flags_cfg = default_runner.get("flags", {})

    return run_route_data_pipeline_v2(
        file_path=input_cfg["file_path"],
        file_seperator=input_cfg.get("file_seperator", ";"),
        route_type=routing_cfg.get("route_type", "both"),
        start_routes=routing_cfg.get("start_routes"),
        max_routes=routing_cfg.get("max_routes"),
        E=algo_cfg.get("E", 5.0),
        z=algo_cfg.get("z", 0.0),
        k_max=algo_cfg.get("k_max", 25),
        k_all=algo_cfg.get("k_all", 1),
        B=algo_cfg.get("B", 10),
        solver_tsp=algo_cfg.get("solver_tsp", "ortools"),
        solver_hpp=algo_cfg.get("solver_hpp", "ortools"),
        deterministic_tsp=algo_cfg.get("deterministic_tsp", True),
        deterministic_hpp=algo_cfg.get("deterministic_hpp", True),
        precheck=algo_cfg.get("precheck", True),
        ortools_time_limit=algo_cfg.get("ortools_time_limit", 5),
        initial_point_method=algo_cfg.get("initial_point_method"),
        type1_methods=algo_cfg.get("type1_methods"),
        type2_methods=algo_cfg.get("type2_methods"),
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
        label_list=label_list,
        APR_profiles=APR_profiles,
        revenue_list=revenue_list,
        save_root=output_cfg.get("save_dir", "./views/application/demo_bus_routes_nyc/data"),
        skip_if_output_exists=flags_cfg.get("skip_if_output_exists", True),
    )


if __name__ == "__main__":
    runtime_path = "./runtime_definitions/application/demo_bus_routes_nyc"
    run_data_from_runtime(runtime_path)
