import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import time
from tqdm import tqdm

from libraries.utils.experiments.simulations import simulate_addresses
from libraries.utils.algorithm.single_route.core_algorithm import find_outliers_hybrid


def benchmark_hybrid_multi(
    n_values: list[int],
    solvers: dict,          
    problem_type: str,
    *,
    seed=834,
    asymmetry_strength=0.2,
    outlier_fraction=0.1,
    ):
    """
    Collect metrics across all n-values and solvers
    for a fixed problem_type (TSP or HPP).

    solvers:
        {
            "ortools": [True, False],
            "greedy": [True],
            ...
        }

    metrics[metric][label] → list over n
    """
    # --------------------------------------------------
    # Expand solver × deterministic into labels
    # --------------------------------------------------
    solver_specs = []
    for solver, det_modes in solvers.items():
        for det in det_modes:
            label = (
                f"{solver} (det={det})"
                if len(det_modes) > 1
                else solver
            )
            solver_specs.append((solver, det, label))
    metrics = {
        "L_original": {label: [] for _, _, label in solver_specs},
        "L_opt":      {label: [] for _, _, label in solver_specs},
        "DG_original":{label: [] for _, _, label in solver_specs},
        "DG_best":    {label: [] for _, _, label in solver_specs},
        "S_out":      {label: [] for _, _, label in solver_specs},
        "C2_max":     {label: [] for _, _, label in solver_specs},
        "time":       {label: [] for _, _, label in solver_specs},
    }
    for n in tqdm(n_values, desc=f"Hybrid simulations ({problem_type})"):
        D, p = simulate_addresses(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
        )
        strict_order = False
        E_used = 5.0
        APR = 0.05
        z = 0.0
        k_all = 1
        k_max = 5
        B = 10
        precheck = True
        methods = ["A", "B", "Beam"]
        A_kwargs = {"method": "kneedle"}
        B_kwargs = {"L_max": 6}
        for solver, deterministic, label in solver_specs:
            try:
                t0 = time.perf_counter()
                (
                    _, _, _, _,
                    L_original,
                    L_opt,
                    S_outlier,
                    C2_max,
                    DG_original,
                    DG_best
                ) = find_outliers_hybrid(
                    D=D,
                    p=p,
                    E=E_used,
                    APR=APR,
                    strict_order=strict_order,
                    z=z,
                    k_all=k_all,
                    k_max=k_max,
                    B=B,
                    precheck=precheck,
                    methods=methods,
                    A_kwargs=A_kwargs,
                    B_kwargs=B_kwargs,
                    deterministic=deterministic,
                    solver=solver,
                    ortools_time_limit=1,
                    problem_type=problem_type,
                )
                t1 = time.perf_counter()
                metrics["L_original"][label].append(L_original)
                metrics["L_opt"][label].append(L_opt)
                metrics["DG_original"][label].append(DG_original)
                metrics["DG_best"][label].append(DG_best)
                metrics["C2_max"][label].append(C2_max)
                metrics["S_out"][label].append(len(S_outlier))
                metrics["time"][label].append(t1 - t0)
            except Exception as e:
                print(f"FAILED solver={solver}, det={deterministic}, n={n}: {e}")
                for key in metrics:
                    metrics[key][label].append(np.nan)
    return metrics

def plot_hybrid_results_multi(n_values, metrics, *, title, save_path):
    solvers = list(metrics["L_original"].keys())

    metric_names = [
        "L_original", "L_opt", "DG_original",
        "DG_best", "S_out", "C2_max", "time"
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
        "Lenght Original vs n",
        "Lenght Optimal vs n",
        "Margin Gain Original vs n",
        "Margin Gain Optimal vs n",
        "|Segnificant Outliers| vs n",
        "Δ Margin Gain vs n",
        "Runtime vs n",
    ]

    # --------------------------------------------------
    # Color map: one color per solver
    # --------------------------------------------------
    cmap = plt.get_cmap("tab10")
    color_map = {
        solver: cmap(i % cmap.N)
        for i, solver in enumerate(solvers)
    }
    fig, axs = plt.subplots(2, len(metric_names), figsize=(34, 10))

    # --------------------------------------------------
    # TOP ROW: curves
    # --------------------------------------------------
    for j, metric in enumerate(metric_names):
        ax = axs[0, j]
        for solver in solvers:
            ax.plot(
                n_values,
                metrics[metric][solver],
                marker="o",
                color=color_map[solver],
                label=solver,  
            )
        ax.set_title(titles[j])
        ax.set_xlabel("n")
        ax.set_ylabel(ylabels[j])
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # --------------------------------------------------
    # BOTTOM ROW: averages (bars)
    # --------------------------------------------------
    for j, metric in enumerate(metric_names):
        ax = axs[1, j]
        avgs = [np.nanmean(metrics[metric][s]) for s in solvers]

        bars = ax.bar(
            range(len(solvers)),
            avgs,
            color=[color_map[s] for s in solvers],
        )
        ax.set_title(f"Avg. {ylabels[j]}")
        ax.grid(axis="y")
        ax.set_xticks([])
        for bar, val in zip(bars, avgs):
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
        plt.Line2D([0], [0], color=color_map[s], marker="o", linestyle="-")
        for s in solvers
    ]
    fig.legend(
        handles,
        solvers,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        title="Solver",
    )
    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0.05, 0.03, 1, 0.95])
    plt.savefig(save_path, dpi=200)
    plt.close()


def main():
    N_MIN = 50
    N_MAX = 100
    n_values = list(range(N_MIN, N_MAX + 1))
    out_dir = "libraries/simulations/_img/benchmarks/hybrid"
    os.makedirs(out_dir, exist_ok=True)
    # -------------------------
    # Hybrid + TSP
    # -------------------------
    TSP_SOLVERS = {
        "greedy": [True],
        "python_tsp": [True, False],
        "ortools": [True, False],
        "lkh": [True],
    }
    metrics_tsp = benchmark_hybrid_multi(
        n_values,
        TSP_SOLVERS,
        problem_type="TSP",
    )
    plot_hybrid_results_multi(
        n_values,
        metrics_tsp,
        title="Hybrid Outlier Detection (TSP)",
        save_path=os.path.join(out_dir, "hybrid_tsp.png"),
    )
    # -------------------------
    # Hybrid + HPP
    # -------------------------
    HPP_SOLVERS = {
        "greedy": [True],
        "greedy_denn": [True],
        "cheapest_insertion": [True],
        "ortools": [True, False],
    }
    metrics_hpp = benchmark_hybrid_multi(
        n_values,
        HPP_SOLVERS,
        problem_type="HPP",
    )
    plot_hybrid_results_multi(
        n_values,
        metrics_hpp,
        title="Hybrid Outlier Detection (HPP)",
        save_path=os.path.join(out_dir, "hybrid_hpp.png"),
    )

if __name__ == "__main__":
    main()
