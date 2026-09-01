import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time

from libraries.utils.algorithm.solvers.hpp import hpp_solve
from libraries.utils.experiments.simulations import simulate_distance_matrix

def benchmark_initial_point_methods(
    n_values,
    initial_point_methods,
    *,
    seed: int = 834,
    asymmetry_strength: float = 0.2,
    outlier_fraction: float = 0.0,
    cluster_strength: float = 0.6,
    fixed_endpoints: dict | None = None,
):
    """
    Run OR-Tools HPP solver for each initial_point_method and n.

    Each initial-point method is evaluated with:
      - deterministic=True
      - deterministic=False

    Returns:
      - length_results : {label: [L(n1), L(n2), ...]}
      - time_results   : {label: [t(n1), t(n2), ...]}
    """

    # --------------------------------------------------
    # Expand methods into (name, cfg, deterministic, label)
    # --------------------------------------------------
    method_specs = []
    for name, cfg in initial_point_methods.items():
        method_specs.append(
            (name, cfg, True, f"{name} (det=T)")
        )
        method_specs.append(
            (name, cfg, False, f"{name}")
        )

    length_results = {label: [] for _, _, _, label in method_specs}
    time_results = {label: [] for _, _, _, label in method_specs}

    for n in tqdm(n_values, desc="Running HPP initial-point study"):
        D = simulate_distance_matrix(
            n=n,
            seed=seed,
            asymmetry_strength=asymmetry_strength,
            outlier_fraction=outlier_fraction,
            cluster_strength=cluster_strength,
        )
        for name, method_cfg, deterministic, label in method_specs:
            try:
                t0 = time.perf_counter()
                _, L = hpp_solve(
                    D,
                    solver="ortools",
                    fixed_endpoints=fixed_endpoints,
                    initial_point_method=method_cfg,
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
    Produce a 2×2 figure:
      1) Path length vs n
      2) Runtime vs n
      3) Average path length
      4) Average runtime
    """
    methods = list(length_results.keys())
    avg_len = [np.nanmean(length_results[m]) for m in methods]
    avg_time = [np.nanmean(time_results[m]) for m in methods]

    _, axs = plt.subplots(2, 2, figsize=(14, 10))

    # -----------------------------------------------------
    # 1) Length vs n
    # -----------------------------------------------------
    ax = axs[0, 0]
    for m, values in length_results.items():
        ax.plot(n_values, values, marker="o", label=m)
    ax.set_title("HPP Path Length vs n (OR-Tools)")
    ax.set_xlabel("n")
    ax.set_ylabel("Path length")
    ax.grid(True)
    ax.legend()

    # -----------------------------------------------------
    # 2) Runtime vs n
    # -----------------------------------------------------
    ax = axs[0, 1]
    for m, values in time_results.items():
        ax.plot(n_values, values, marker="o", label=m)
    ax.set_title("OR-Tools Runtime vs n (Initial-point methods)")
    ax.set_xlabel("n")
    ax.set_ylabel("Runtime (seconds)")
    ax.grid(True)
    ax.legend()

    # -----------------------------------------------------
    # 3) Average path length
    # -----------------------------------------------------
    ax = axs[1, 0]
    x = np.arange(len(methods))
    bars = ax.bar(x, avg_len, color="steelblue")
    ax.set_title("Average HPP Path Length")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=20)
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
    ax.set_title("Average OR-Tools Runtime")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=20)
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

def main():
    N_MIN = 50
    N_MAX = 100
    n_values = list(range(N_MIN, N_MAX + 1))
    # -----------------------------------------------------
    # Initial-point methods to compare (EXTENDED_SEARCH is not included cause it will "allways win" but running time will be long)
    # -----------------------------------------------------
    initial_point_methods = {
        "INDEX": {"method": "INDEX"},
        "GREEDY": {"method": "GREEDY"},
        "GREEDY_DNN": {"method": "GREEDY_DNN"},
        "FURTHEST_AWAY": {"method": "FURTHEST_AWAY", "n_edges": 2},
        #"EXTENDED_SEARCH": {"method": "EXTENDED_SEARCH", "n_iterations": 1,"time_limit": 1}, 
    }
    fixed_endpoints = {"start": None, "end": None}
    length_results, time_results = benchmark_initial_point_methods(
        n_values,
        initial_point_methods,
        fixed_endpoints=fixed_endpoints,
    )
    plot_all_results(
        n_values,
        length_results,
        time_results,
        save_path="libraries/simulations/_img/benchmarks/hpp/hpp_ortools_initial_point_study.png",
    )


if __name__ == "__main__":
    main()
