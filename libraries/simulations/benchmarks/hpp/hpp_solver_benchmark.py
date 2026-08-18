import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
from libraries.utils.algorithm.solvers.hpp import hpp_solve
from libraries.utils.experiments.simulations import simulate_distance_matrix


def benchmark_hpp_solvers(
    n_values,
    solvers,
    initial_point_method,
    *,
    seed: int = 834,
    asymmetry_strength: float = 0.2,
    outlier_fraction: float = 0.0,
    cluster_strength=0.6,
    fixed_endpoints: dict | None = None,
    ):
    """
    Run all HPP solvers for each n.

    For OR-Tools, run both:
      - deterministic=True
      - deterministic=False

    Other solvers are always deterministic.

    Returns:
      - length_results : {label: [L(n1), L(n2), ...]}
      - time_results   : {label: [t(n1), t(n2), ...]}
    """
    solver_specs = []
    for solver in solvers:
        if solver == "ortools":
            solver_specs.append(
                ("ortools", True, "ortools (det=T)")
            )
            solver_specs.append(
                ("ortools", False, "ortools")
            )
        else:
            solver_specs.append(
                (solver, True, solver)
            )
    length_results = {label: [] for _, _, label in solver_specs}
    time_results = {label: [] for _, _, label in solver_specs}
    for n in tqdm(n_values, desc="Running HPP simulations"):
        D = simulate_distance_matrix(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
            cluster_strength=cluster_strength,
        )
        for solver, deterministic, label in solver_specs:
            try:
                t0 = time.perf_counter()
                _, L = hpp_solve(
                    D,
                    solver=solver,
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=initial_point_method,
                    ortools_time_limit=2,
                    deterministic=deterministic,
                )
                t1 = time.perf_counter()
                length_results[label].append(L)
                time_results[label].append(t1 - t0)
            except Exception as e:
                print(f"FAILED ({label}, n={n}): {e}")
                length_results[label].append(np.nan)
                time_results[label].append(np.nan)
    return length_results, time_results


def plot_all_results(n_values, length_results, time_results, save_path: str):
    """
    Produce a 2×2 subplot figure showing:
      1) Path length vs n
      2) Runtime vs n
      3) Average path length (bar plot)
      4) Average runtime (bar plot)
    """
    solvers = list(length_results.keys())
    avg_len = [np.nanmean(length_results[s]) for s in solvers]
    avg_time = [np.nanmean(time_results[s]) for s in solvers]
    _, axs = plt.subplots(2, 2, figsize=(14, 10))
    # -----------------------------------------------------
    # 1) Length vs n
    # -----------------------------------------------------
    ax = axs[0, 0]
    for solver, values in length_results.items():
        ax.plot(n_values, values, marker="o", label=solver)
    ax.set_title("HPP Path Length vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Path length")
    ax.grid(True)
    ax.legend()
    # -----------------------------------------------------
    # 2) Runtime vs n
    # -----------------------------------------------------
    ax = axs[0, 1]
    for solver, values in time_results.items():
        ax.plot(n_values, values, marker="o", label=solver)
    ax.set_title("HPP Solver Runtime vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Runtime (seconds)")
    ax.grid(True)
    ax.legend()
    # -----------------------------------------------------
    # 3) Average path length
    # -----------------------------------------------------
    ax = axs[1, 0]
    x = np.arange(len(solvers))
    bars = ax.bar(x, avg_len, color="steelblue")
    ax.set_title("Average HPP Path Length Across n")
    ax.set_xticks(x)
    ax.set_xticklabels(solvers)
    ax.set_ylabel("Average path length")
    ax.grid(axis="y")
    for bar, val in zip(bars, avg_len):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    # -----------------------------------------------------
    # 4) Average runtime
    # -----------------------------------------------------
    ax = axs[1, 1]
    bars = ax.bar(x, avg_time, color="darkorange")
    ax.set_title("Average Solver Runtime Across n")
    ax.set_xticks(x)
    ax.set_xticklabels(solvers)
    ax.set_ylabel("Average runtime (seconds)")
    ax.grid(axis="y")
    for bar, val in zip(bars, avg_time):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def main(N_MIN = 50,
         N_MAX = 100):
    solvers = [
        "greedy",    
        "greedy_denn",           
        "cheapest_insertion",   
        "ortools",              
    ]
    initial_point_method = {"method": "GREEDY_DNN"}
    n_values = list(range(N_MIN, N_MAX + 1))
    fixed_endpoints = {"start": None, "end": None}
    length_results, time_results = benchmark_hpp_solvers(
        n_values,
        solvers,
        initial_point_method=initial_point_method,
        fixed_endpoints=fixed_endpoints,
    )
    plot_all_results(
        n_values,
        length_results,
        time_results,
        save_path="libraries/simulations/_img/benchmarks/hpp/hpp_solver_benchmark.png",
    )


if __name__ == "__main__":
    main()