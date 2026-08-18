import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from tqdm import tqdm
from typing import Dict, List, Iterable
from collections import defaultdict

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.algorithm.single_route.core_algorithm import (
    find_outliers,
    find_outliers_hybrid,
)

# ============================================================
# Utility scores
# ============================================================

def jaccard_score(a: Iterable[int], b: Iterable[int]) -> float:
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

def ratio_score(x: float, y: float) -> float:
    if x == y:
        return 1.0
    return min(x, y) / max(x, y, 1e-12)

def _method_label(methods: List[str]) -> str:
    return "plain" if not methods else "+".join(methods)

def _solver_label(solver: str, det: bool, det_modes: List[bool]) -> str:
    return f"{solver}|det={det}" if len(det_modes) > 1 else solver

def _safe_filename(s: str) -> str:
    return (
        s.replace("|", "_")
         .replace("=", "")
         .replace(" ", "_")
         .replace("/", "_")
    )

# ============================================================
# Validation routine
# ============================================================
def validate_outliers_vs_exact(
    *,
    problem_type: str,
    solvers: Dict[str, List[bool]],
    method_sets: List[List[str]],
    n_values: List[int],
    repeats: int = 10,
    seed: int = 834,
    asymmetry_strength: float = 0.2,
    outlier_fraction: float = 0.2,
    ):
    """
    Validates outlier detection against an exact baseline.

    Exact baseline:
        find_outliers(..., solver="exact")
    Test variants:
        find_outliers_hybrid(..., methods=METHOD_SET, solver=SOLVER, deterministic=DET)

    Returns a nested structure keyed to enable "one figure per solver":
        results[route_type][solver_label][method_label][metric]["by_n"][n] -> list[float]
        results[route_type][solver_label][method_label][metric]["all"]      -> list[float]

    Where:
        route_type in {"Type1", "Type2"}
        solver_label:
            - Type1 only: "Type1"
            - Type2: e.g. "ortools|det=True"
        metric in {"score_S","score_L","score_C2"}
    """
    rng = np.random.default_rng(seed)
    def _empty_method_metric():
        return {"by_n": defaultdict(list), "all": []}
    results = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(_empty_method_metric)
            )
        )
    )
    for strict_order in [True, False]:
        route_type = "Type1" if strict_order else "Type2"
        print(f"\n=== Outlier validation: {problem_type} / {route_type} ===")
        for n in tqdm(n_values, desc=f"{problem_type} {route_type}"):
            for _ in range(repeats):
                D, p = simulate_addresses(
                    n=n,
                    seed=int(rng.integers(0, 1e9)),
                    asymmetry_strength=asymmetry_strength,
                    outlier_fraction=outlier_fraction,
                )
                E = 5.0
                APR = 0.05
                z = 0.0
                # --------------------------------------------------
                # Exact baseline (ground truth)
                # --------------------------------------------------
                (
                    _, _, _, _,
                    _, L_exact,
                    S_exact,
                    C2_exact,
                    _, _
                ) = find_outliers(
                    D=D,
                    p=p,
                    E=E,
                    APR=APR,
                    strict_order=strict_order,
                    z=z,
                    solver="exact",
                    deterministic=True,
                    problem_type=problem_type,
                )
                # --------------------------------------------------
                # Which "solvers" exist?
                #   - Type1: no solver choice => single "Type1"
                #   - Type2: solver × deterministic modes
                # --------------------------------------------------
                solver_specs = []
                if strict_order:
                    solver_specs = [("Type1", True, "Type1")]
                else:
                    for solver, det_modes in solvers.items():
                        for det in det_modes:
                            solver_specs.append((solver, det, _solver_label(solver, det, det_modes)))
                # --------------------------------------------------
                # Evaluate method sets
                # --------------------------------------------------
                for methods in method_sets:
                    mlabel = _method_label(methods)
                    for solver, det, slabel in solver_specs:
                        (
                            _, _, _, _,
                            _, L_test,
                            S_test,
                            C2_test,
                            _, _
                        ) = find_outliers_hybrid(
                            D=D,
                            p=p,
                            E=E,
                            APR=APR,
                            strict_order=strict_order,
                            z=z,
                            solver=("greedy" if solver == "Type1" else solver),
                            deterministic=det,
                            methods=methods,
                            precheck=True,
                            problem_type=problem_type,
                        )
                        sS = jaccard_score(S_test, S_exact)
                        sL = ratio_score(L_test, L_exact)
                        sC2 = ratio_score(C2_test, C2_exact)
                        for metric, val in [
                            ("score_S", sS),
                            ("score_L", sL),
                            ("score_C2", sC2),
                        ]:
                            results[route_type][slabel][mlabel][metric]["by_n"][n].append(val)
                            results[route_type][slabel][mlabel][metric]["all"].append(val)
    return results

# ============================================================
# Plotting: one figure per solver (4 rows × 3 metrics)
# ============================================================
def plot_validation_per_solver(
    *,
    solver_data: dict,  # solver_data[method][metric] -> {"by_n": {n: [...]}, "all": [...]}
    problem_type: str,
    route_type: str,
    solver_label: str,
    n_values: list[int],
    save_path: str,
):
    """
    ONE figure per solver with:
      - Row 1: mean score vs n
      - Row 2: average score per method
      - Row 3: distribution (boxplots)
      - Row 4: quantile tables (one per metric)

    Y-axis policy:
      - Shared within rows
      - Independent across rows
    """
    metrics = [
        ("score_S", "Outlier Set Agreement (Jaccard)"),
        ("score_L", "L_opt Agreement (ratio)"),
        ("score_C2", "C2_max Agreement (ratio)"),
    ]
    methods = list(solver_data.keys())

    cmap = plt.get_cmap("tab10")
    color_map = {m: cmap(i % cmap.N) for i, m in enumerate(methods)}

    def _finite(x):
        a = np.asarray(x, dtype=float)
        return a[np.isfinite(a)]

    # --------------------------------------------------
    # Precompute all statistics
    # --------------------------------------------------
    stats = {}
    for metric_key, _ in metrics:
        stats[metric_key] = {}
        for m in methods:
            vals = _finite(solver_data[m][metric_key]["all"])
            if vals.size == 0:
                stats[metric_key][m] = None
            else:
                stats[metric_key][m] = {
                    "min": np.min(vals),
                    "q25": np.percentile(vals, 25),
                    "median": np.median(vals),
                    "q75": np.percentile(vals, 75),
                    "max": np.max(vals),
                    "mean": np.mean(vals),
                }

    # --------------------------------------------------
    # Compute row-wise y-limits
    # --------------------------------------------------
    def _row_ylim(metric_key):
        all_vals = np.concatenate([
            _finite(solver_data[m][metric_key]["all"])
            for m in methods
            if _finite(solver_data[m][metric_key]["all"]).size > 0
        ])
        if all_vals.size == 0:
            return (0.0, 1.02)
        y0 = max(0.0, np.min(all_vals) - 0.02)
        y1 = min(1.02, np.max(all_vals) + 0.01)
        if (y1 - y0) < 0.05:
            mid = 0.5 * (y0 + y1)
            y0 = max(0.0, mid - 0.05)
            y1 = min(1.02, mid + 0.05)
        return y0, y1

    ylim_line = _row_ylim("score_S")
    ylim_bar  = _row_ylim("score_L")
    ylim_box  = _row_ylim("score_C2")

    # --------------------------------------------------
    # Figure layout: 4 rows × 3 columns
    # --------------------------------------------------
    fig, axs = plt.subplots(
        4, len(metrics),
        figsize=(28, 18),
        gridspec_kw={"height_ratios": [2.5, 1.8, 2.2, 1.2]},
    )

    fig.suptitle(
        f"Outlier Validation vs Exact — {problem_type} / {route_type} / {solver_label}",
        fontsize=16,
    )

    # ==================================================
    # Row 1: Mean vs n
    # ==================================================
    for j, (metric_key, metric_title) in enumerate(metrics):
        ax = axs[0, j]
        for m in methods:
            means = []
            for n in n_values:
                vals = _finite(solver_data[m][metric_key]["by_n"].get(n, []))
                means.append(np.mean(vals) if vals.size else np.nan)

            ax.plot(
                n_values, means,
                marker="o",
                linewidth=2,
                color=color_map[m],
                label=m,
            )

        ax.axhline(1.0, color="black", linestyle="--", linewidth=1, alpha=0.6)
        ax.set_title(f"{metric_title} vs n")
        ax.set_xlabel("n")
        ax.set_ylabel("Score")
        ax.set_ylim(*ylim_line)
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # ==================================================
    # Row 2: Average per method
    # ==================================================
    for j, (metric_key, metric_title) in enumerate(metrics):
        ax = axs[1, j]
        avgs = [
            stats[metric_key][m]["mean"]
            if stats[metric_key][m] is not None else np.nan
            for m in methods
        ]

        bars = ax.bar(
            range(len(methods)),
            avgs,
            color=[color_map[m] for m in methods],
        )

        ax.set_title(f"Avg. {metric_title}")
        ax.set_ylabel("Average score")
        ax.set_ylim(*ylim_bar)
        ax.set_xticks([])
        ax.grid(axis="y")

        for bar, val in zip(bars, avgs):
            if np.isfinite(val):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    # ==================================================
    # Row 3: Boxplots + all observations
    # ==================================================
    for j, (metric_key, metric_title) in enumerate(metrics):
        ax = axs[2, j]

        data = []
        for m in methods:
            vals = _finite(solver_data[m][metric_key].get("all", []))
            if vals.size == 0:
                vals = np.array([np.nan])
            data.append(vals)

        # --- boxplot ---
        bp = ax.boxplot(
            data,
            tick_labels=methods,
            patch_artist=True,
            showfliers=False,
            widths=0.6,
        )

        for patch, m in zip(bp["boxes"], methods):
            patch.set_facecolor(color_map[m])
            patch.set_alpha(0.5)

        # --- overlay ALL observations (jittered) ---
        for i, vals in enumerate(data, start=1):
            if len(vals) == 0:
                continue
            x = np.random.normal(i, 0.04, size=len(vals))
            ax.plot(
                x,
                vals,
                "o",
                color="black",
                alpha=0.35,
                markersize=3,
                zorder=3,
            )

        ax.set_title(f"Distribution of {metric_title}")
        ax.set_ylabel("Score")
        ax.set_ylim(*ylim_box)   # keep your semantic boxplot range
        ax.grid(axis="y")
        ax.tick_params(axis="x", rotation=30)
        ax.set_autoscale_on(False)

    # ==================================================
    # Row 4: Quantile tables
    # ==================================================
    for j, (metric_key, metric_title) in enumerate(metrics):
        ax = axs[3, j]
        ax.axis("off")
        ax.text(
            0.5,
            1.05,
            f"{metric_title} — Quantiles",
            ha="center",
            va="bottom",
            fontsize=11,
            transform=ax.transAxes,
        )
        col_labels = ["Min", "Q25", "Median", "Q75", "Max"]
        cell_text = []
        for m in methods:
            s = stats[metric_key][m]
            if s is None:
                cell_text.append(["–"] * 5)
            else:
                cell_text.append([
                    f"{s['min']:.3f}",
                    f"{s['q25']:.3f}",
                    f"{s['median']:.3f}",
                    f"{s['q75']:.3f}",
                    f"{s['max']:.3f}",
                ])
        table = ax.table(
            cellText=cell_text,
            rowLabels=methods,
            colLabels=col_labels,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, 1.4)

    # --------------------------------------------------
    # Global legend
    # --------------------------------------------------
    handles = [
        plt.Line2D([0], [0], color=color_map[m], marker="o", linestyle="-")
        for m in methods
    ]
    fig.legend(
        handles,
        methods,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        title="Method set",
    )

    plt.tight_layout(rect=[0.05, 0.03, 1, 0.95])
    plt.savefig(save_path, dpi=200)
    plt.close()

# ============================================================
# Main
# ============================================================
def main():
    PROBLEM_TYPES = ["TSP", "HPP"]
    N_VALUES = list(range(5, 11))  # n <= 10 (adjust as needed)
    REPEATS = 10
    SOLVERS_TSP = {
        "greedy": [True],
        "python_tsp": [True, False],
        "ortools": [True, False],
        "lkh": [True],
    }
    SOLVERS_HPP = {
        "greedy": [True],
        "greedy_denn": [True],
        "cheapest_insertion": [True],
        "ortools": [True, False],
    }
    METHOD_SETS = [
        [],
        ["A"],
        ["B"],
        ["Beam"],
        ["A", "B"],
        ["A", "Beam"],
        ["B", "Beam"],
        ["A", "B", "Beam"],
    ]
    base_outdir = "libraries/simulations/_img/validation/outliers"
    os.makedirs(base_outdir, exist_ok=True)
    for problem_type in PROBLEM_TYPES:
        problem_dir = os.path.join(base_outdir, problem_type.lower())
        os.makedirs(problem_dir, exist_ok=True)
        solvers = SOLVERS_TSP if problem_type == "TSP" else SOLVERS_HPP
        # --------------------------------------------------
        # Validate (returns Type1 and Type2 results)
        # --------------------------------------------------
        results = validate_outliers_vs_exact(
            problem_type=problem_type,
            solvers=solvers,
            method_sets=METHOD_SETS,
            n_values=N_VALUES,
            repeats=REPEATS,
        )
        # --------------------------------------------------
        # One figure per solver (and route type)
        #   Type1: solver_label == "Type1"
        #   Type2: solver_label == "greedy|det=True", etc.
        # --------------------------------------------------
        for route_type in ["Type1", "Type2"]:
            route_dir = os.path.join(problem_dir, route_type.lower())
            os.makedirs(route_dir, exist_ok=True)

            for solver_label, solver_data in results[route_type].items():
                fname = f"{_safe_filename(solver_label)}.png"
                save_path = os.path.join(route_dir, fname)
                plot_validation_per_solver(
                    solver_data=solver_data,
                    problem_type=problem_type,
                    route_type=route_type,
                    solver_label=solver_label,
                    n_values=N_VALUES,
                    save_path=save_path,
                )
                print(f"Saved: {save_path}")

if __name__ == "__main__":
    main()
