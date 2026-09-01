import os
import json
from typing import Dict, Any, List, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from libraries.utils.pipelines.pipelines.static.v1.run_route_presentation_pipeline import (
    run_route_presentation_pipeline
)

# ============================================================
# PATHS
# ============================================================

DATA_DIR = "libraries/simulations/_data/routes"
TSP_DATA = os.path.join(DATA_DIR, "tsp_simulationdata.csv")
HPP_DATA = os.path.join(DATA_DIR, "hpp_simulationdata.csv")
RUNNER_JSON_PATH = "libraries/simulations/_data/runners/runner.json"  # optional runner defaults
IMG_PATH = "libraries/simulations/_img/benchmarks/hybrid"

# ============================================================
# SOLVERS
# ============================================================

TSP_SOLVERS = ["greedy", "python_tsp", "ortools", "lkh"]
HPP_SOLVERS = ["greedy", "greedy_denn", "ortools"] # ,"cheapest_insertion"]

DETERMINISTIC_MODES = {
    "TSP": {
        "greedy": [True],
        "python_tsp": [True, False],
        "ortools": [True, False],
        "lkh": [True],
    },
    "HPP": {
        "greedy": [True],
        "greedy_denn": [True],
        "cheapest_insertion": [True],
        "ortools": [True, False],
    },
}


# ============================================================
# LOAD RUNNER DEFAULTS
# ============================================================

def load_runner_defaults(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_pipeline_kwargs(runner: Dict[str, Any]) -> Dict[str, Any]:
    alg = runner.get("algorithm", {})
    routing = runner.get("routing", {})
    output = runner.get("output", {})
    
    return {
        "E": alg.get("E", 5.0),
        "APR": alg.get("APR", 0.03),
        "z": alg.get("z", 0.0),
        "k_max": alg.get("k_max", 25),
        "k_all": alg.get("k_all", 1),
        "B": alg.get("B", 10),
        "precheck": alg.get("precheck", True),
        "A_kwargs": alg.get("A_kwargs", {"method": "kneedle"}),
        "B_kwargs": alg.get("B_kwargs", {"L_max": 8}),
        "type1_methods": alg.get("type1_methods", ["A", "B", "Beam"]),
        "type2_methods": alg.get("type2_methods", ["A", "B"]),
        "ortools_time_limit": alg.get("ortools_time_limit", 2),
        "initial_point_method": alg.get("initial_point_method", None),
        "start_routes": routing.get("start_routes", None),
        "html_render": output.get("html_render", False),
        "col_map": runner.get("col_map", None),
        "kpi_mapping": runner.get("kpis", []),
    }

# ============================================================
# CONFIG GENERATION 
# ============================================================

def build_configs_for_problem(problem: str) -> List[Dict[str, Any]]:
    configs: List[Dict[str, Any]] = []
    # ---------- TYPE 1 (baseline, once) ----------
    configs.append({
        "name": f"{problem} | Type 1",
        "problem": problem,
        "route_type": "type1",
        "solver": None,
        "deterministic_tsp": True,
        "deterministic_hpp": True,
    })
    # ---------- TYPE 2 (solver-dependent) ----------
    solvers = TSP_SOLVERS if problem == "TSP" else HPP_SOLVERS
    for solver in solvers:
        det_modes = DETERMINISTIC_MODES[problem][solver]
        for det in det_modes:
            label = (
                f"{problem} | Type 2 | {solver}"
                if det_modes == [True]
                else f"{problem} | Type 2 | {solver} | det={det}"
            )
            configs.append({
                "name": label,
                "problem": problem,
                "route_type": "type2",
                "solver": solver,
                "deterministic_tsp": det,
                "deterministic_hpp": det,
            })
    return configs

# ============================================================
# RUN ALL CONFIGS
# ============================================================

def run_all_configs(
    configs: List[Dict[str, Any]],
    *,
    pipeline_kwargs: Dict[str, Any],
    max_routes_override: Optional[int],
) -> Dict[str, Dict[str, Any]]:

    output: Dict[str, Dict[str, Any]] = {}

    for cfg in configs:
        name = cfg["name"]
        print(f"\nRunning {name}")

        if cfg["problem"] == "TSP":
            file_path = TSP_DATA
            solver_tsp = cfg["solver"]
            solver_hpp = None
            det_tsp = cfg["deterministic_tsp"]
            det_hpp = True
        else:
            file_path = HPP_DATA
            solver_tsp = None
            solver_hpp = cfg["solver"]
            det_tsp = True
            det_hpp = cfg["deterministic_hpp"]

        max_routes = (
            max_routes_override
            if max_routes_override is not None
            else pipeline_kwargs.get("max_routes", None)
        )
        results, _ = run_route_presentation_pipeline(
            file_path=file_path,
            route_type=cfg["route_type"],
            solver_tsp=solver_tsp,
            solver_hpp=solver_hpp,
            deterministic_tsp=det_tsp,
            deterministic_hpp=det_hpp,
            max_routes=max_routes,
            **pipeline_kwargs,
        )
        output[name] = {
            "results": results,   
            "meta": cfg,
        }
    return output

# ============================================================
# KPI EXTRACTION
# ============================================================

def extract_kpis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "route_ids": [r["route_id"] for r in results],

        "L_original": [r.get("L_original", np.nan) for r in results],
        "L_opt":      [r.get("L_opt", np.nan) for r in results],
        "DG_original": [r.get("DG_original", np.nan) for r in results],
        "DG_best":     [r.get("DG_best", np.nan) for r in results],
        "outliers": [
            len(r["S_outlier"]) if r.get("S_outlier") is not None else np.nan
            for r in results
        ],
        "C2_max": [r.get("C2_max", np.nan) for r in results],
        "runtime": [r.get("runtime", np.nan) for r in results],
    }

def build_plot_data(raw: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    plot_data = {}
    for name, entry in raw.items():
        kpis = extract_kpis(entry["results"])
        kpis["meta"] = entry["meta"]
        plot_data[name] = kpis
    return plot_data

# ============================================================
# PLOTTING (ONE FIGURE PER PROBLEM)
# ============================================================

def plot_problem(plot_data: Dict[str, Dict[str, Any]], *, problem: str, save_path: str):
    keys = [k for k, v in plot_data.items() if v["meta"]["problem"] == problem]
    route_ids = plot_data[keys[0]]["route_ids"]

    metrics = [
        "L_original",
        "L_opt",
        "DG_original",
        "DG_best",
        "outliers",
        "C2_max",
        "runtime",
    ]

    ylabels = [
        "Length Original",
        "Length Optimal",
        "Margin Gain Original",
        "Margin Gain Optimal",
        "|Significant Outliers|",
        "Δ Margin Gain",
        "Runtime (s)",
    ]

    titles = [
        "Length Original vs route",
        "Length Optimal vs route",
        "Margin Gain Original vs route",
        "Margin Gain Optimal vs route",
        "|Significant Outliers| vs route",
        "Δ Margin Gain vs route",
        "Runtime vs route",
    ]

    # --------------------------------------------------
    # Color map: one color per method
    # --------------------------------------------------
    cmap = plt.get_cmap("tab10")
    color_map = {
        k: cmap(i % cmap.N)
        for i, k in enumerate(keys)
    }
    fig, axs = plt.subplots(2, len(metrics), figsize=(34, 10))
    fig.suptitle(
        f"{problem}: Metric × Route (top) and Avg per Method (bottom)",
        fontsize=16,
    )

    # --------------------------------------------------
    # TOP ROW: Metric × route index
    # --------------------------------------------------
    for j, metric in enumerate(metrics):
        ax = axs[0, j]
        for k in keys:
            vals = plot_data[k][metric]
            ax.plot(
                route_ids,
                vals,
                marker="o",
                color=color_map[k],
                label=k,   
            )
        ax.set_title(titles[j])
        ax.set_xlabel("Route index")
        ax.set_ylabel(ylabels[j])
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # --------------------------------------------------
    # BOTTOM ROW: Averages (bars)
    # --------------------------------------------------
    for j, metric in enumerate(metrics):
        ax = axs[1, j]
        avgs = [
            float(np.nanmean(plot_data[k][metric]))
            if np.any(~np.isnan(plot_data[k][metric]))
            else np.nan
            for k in keys
        ]
        bars = ax.bar(
            range(len(keys)),
            avgs,
            color=[color_map[k] for k in keys],
        )
        ax.set_title(f"Avg. {ylabels[j]}")
        ax.grid(axis="y")
        ax.set_xticks([])
        for bar, val in zip(bars, avgs):
            if not np.isnan(val):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    # --------------------------------------------------
    # SINGLE GLOBAL LEGEND (top-left)
    # --------------------------------------------------
    handles = [
        plt.Line2D([0], [0], color=color_map[k], marker="o", linestyle="-")
        for k in keys
    ]

    fig.legend(
        handles,
        keys,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        title="Method",
    )

    plt.tight_layout(rect=[0.05, 0.03, 1, 0.95])
    plt.savefig(save_path, dpi=200)
    plt.close()


# ============================================================
# MAIN (TSP RUN + HPP RUN)
# ============================================================

if __name__ == "__main__":
    MAX_ROUTES = 10
    runner = load_runner_defaults(RUNNER_JSON_PATH)
    pipeline_kwargs = build_pipeline_kwargs(runner)
    pipeline_kwargs["html_render"] = False
    os.makedirs(IMG_PATH, exist_ok=True)
    # ---------------- TSP ----------------
    tsp_configs = build_configs_for_problem("TSP")
    tsp_raw = run_all_configs(
        tsp_configs,
        pipeline_kwargs=pipeline_kwargs,
        max_routes_override=MAX_ROUTES,
    )
    tsp_plot_data = build_plot_data(tsp_raw)
    plot_problem(
        tsp_plot_data,
        problem="TSP",
        save_path=os.path.join(IMG_PATH, "hybrid_tsp_routes.png"),
    )

    # ---------------- HPP ----------------
    hpp_configs = build_configs_for_problem("HPP")
    hpp_raw = run_all_configs(
        hpp_configs,
        pipeline_kwargs=pipeline_kwargs,
        max_routes_override=MAX_ROUTES,
    )
    hpp_plot_data = build_plot_data(hpp_raw)
    print(hpp_plot_data)
    plot_problem(
        hpp_plot_data,
        problem="HPP",
        save_path=os.path.join(IMG_PATH, "hybrid_hpp_routes.png"),
    )
    print("\n[INFO] Finished successfully.")