import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
from libraries.utils.algorithm.solvers.tsp import tsp_solve
from libraries.utils.experiments.simulations import simulate_distance_matrix

def _normalize_solvers(solvers):
    if isinstance(solvers, dict):
        return solvers
    return {solver: [True] for solver in solvers}

def benchmark_solvers(n_values, 
                      solvers, 
                      seed: int = 834, 
                      asymmetry_strength: float = 0.2, 
                      outlier_fraction: float = 0.0,
                      cluster_strength: float =0.6):
    """
    Run all solvers for each n and return:
      - length_results : {solver: [L(n1), L(n2), ...]}
      - time_results   : {solver: [t(n1), t(n2), ...]}
    """
    solvers = _normalize_solvers(solvers)
    solver_labels = [
        f"{solver} | det={det}" if len(det_modes) > 1 else solver
        for solver, det_modes in solvers.items()
        for det in det_modes
    ]
    length_results = {label: [] for label in solver_labels}
    time_results   = {label: [] for label in solver_labels}
    for n in tqdm(n_values, desc="Running simulations"):
        D = simulate_distance_matrix(
                n=n,
                seed=seed,
                asymmetry_strength=asymmetry_strength,
                outlier_fraction = outlier_fraction,
                cluster_strength=cluster_strength,
        )
        for solver, det_modes in solvers.items():
            for det in det_modes:
                label = f"{solver} | det={det}" if len(det_modes) > 1 else solver
                try:
                    t0 = time.perf_counter()
                    _, L = tsp_solve(
                        D,
                        deterministic_tsp=det,
                        solver=solver,
                        ortools_time_limit=2,
                    )
                    t1 = time.perf_counter()
                    length_results[label].append(L)
                    time_results[label].append(t1 - t0)
                except Exception as e:
                    print(f"FAILED ({solver}, det={det}, n={n}): {e}")
                    length_results[label].append(np.nan)
                    time_results[label].append(np.nan)
    return length_results, time_results

def plot_all_results(n_values, length_results, time_results,save_path):
    """
    Produce a 2×2 subplot figure showing:
      1) Tour length vs n
      2) Runtime vs n
      3) Average tour length (bar plot with values)
      4) Average runtime (bar plot with values)
    """
    solvers = list(length_results.keys())
    avg_len  = [np.nanmean(length_results[s]) for s in solvers]
    avg_time = [np.nanmean(time_results[s]) for s in solvers]
    _, axs = plt.subplots(2, 2, figsize=(14, 10))
    # -----------------------------------------------------
    # 1) Length vs n
    # -----------------------------------------------------
    ax = axs[0, 0]
    for solver, values in length_results.items():
        ax.plot(n_values, values, marker="o", label=solver)
    ax.set_title("TSP Tour Length vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Tour length")
    ax.grid(True)
    ax.legend()
    # -----------------------------------------------------
    # 2) Runtime vs n
    # -----------------------------------------------------
    ax = axs[0, 1]
    for solver, values in time_results.items():
        ax.plot(n_values, values, marker="o", label=solver)
    ax.set_title("TSP Solver Runtime vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Runtime (seconds)")
    ax.grid(True)
    ax.legend()
    # -----------------------------------------------------
    # 3) Average tour length (with labels)
    # -----------------------------------------------------
    ax = axs[1, 0]
    x = np.arange(len(solvers))
    bars = ax.bar(x, avg_len, color="steelblue")
    ax.set_title("Average TSP Tour Length Across n")
    ax.set_xticks(x)
    ax.set_xticklabels(solvers, rotation=25, ha="right")
    ax.set_ylabel("Average tour length")
    ax.grid(axis='y')
    for bar, val in zip(bars, avg_len):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=10
        )
    # -----------------------------------------------------
    # 4) Average runtime (with labels)
    # -----------------------------------------------------
    ax = axs[1, 1]
    bars = ax.bar(x, avg_time, color="darkorange")
    ax.set_title("Average Solver Runtime Across n")
    ax.set_xticks(x)
    ax.set_xticklabels(solvers, rotation=25, ha="right")
    ax.set_ylabel("Average runtime (seconds)")
    ax.grid(axis='y')
    for bar, val in zip(bars, avg_time):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.4f}",
            ha="center",
            va="bottom",
            fontsize=10
        )
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def main():
    N_MIN = 50
    N_MAX = 100
    solvers = {
        "greedy": [True],
        "python_tsp": [True, False],
        "ortools": [True, False],
        "lkh": [True],
    }
    n_values = list(range(N_MIN, N_MAX + 1))
    length_results, time_results = benchmark_solvers(n_values, solvers)
    plot_all_results(n_values, 
                     length_results, 
                     time_results,
                     save_path="libraries/simulations/_img/benchmarks/tsp/tsp_solver_benchmark.png",)

if __name__ == "__main__":
    main()
