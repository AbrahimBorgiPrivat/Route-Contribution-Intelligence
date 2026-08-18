import time
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm
from collections import defaultdict
from typing import Dict, List, Literal, Any
from matplotlib.ticker import MaxNLocator

from libraries.utils.experiments.simulations import simulate_distance_matrix
from libraries.utils.algorithm.single_route.route_solver import solve_route

def _solver_id(solver: str, deterministic: bool) -> str:
    return f"{solver}|det={deterministic}"

# ---------------------------------------------------------
# Main validation routine
# ---------------------------------------------------------
def validate_exact_vs_heuristic(
    *,
    problem_types: Literal["TSP", "HPP"],
    n_values: List[int],
    DETERMINISTIC_MODES: dict,
    n_instances: int = 10,
    seed: int = 834,
    asymmetry_strength: float = 0.2,
    outlier_fraction: float = 0.0,
    cluster_strength: float = 0.6,
    fixed_endpoints: Dict[str, int | None] | None = None,
    ):
    """
    Validate heuristic solvers against exact solutions using solve_route().
    This function performs *ground-truth validation*, not benchmarking.

    Parameters
    ----------
    problem_types : Problem types to validate.
    n_values : Route sizes (should be <= 20 due to exact solver).
    n_instances : Number of random instances per n.
    seed : Base random seed.
    asymmetry_strength : Degree of asymmetry in simulated matrices.
    outlier_fraction : Fraction of outlier nodes.
    cluster_strength : Degree of spatial clustering.
    fixed_endpoints : Fixed endpoints for HPP (passed through solve_route).

    Returns
    -------
    results : 
        Nested structure:
        results[problem_type][n][solver_id] = {
            "gap":           [relative optimality gaps],
            "exact_match":   [bool],
            "runtime":       [seconds],
            "L":             [route lengths],
            "L_exact":       [exact route lengths],
        }

        where:
            solver_id = "<solver>|det=<True|False>"

    Notes
    -----
    - solver="exact" is used as the ground-truth baseline.
    - exact solver is deterministic and exponential-time.
    - Validation is only meaningful for small n.
    """

    if fixed_endpoints is None:
        fixed_endpoints = {"start": None, "end": None}
    results = {
        problem_type: {
            n: defaultdict(lambda: defaultdict(list))
            for n in n_values
        }
        for problem_type in problem_types
    }
    for problem_type in problem_types:
        print(f"\n=== VALIDATING {problem_type} ===")
        solver_modes = DETERMINISTIC_MODES[problem_type]
        for n in tqdm(n_values, desc=f"{problem_type} validation",leave=False):
            for k in tqdm(range(n_instances), desc=f"Instance in {problem_type} for n={n}", leave=False):
                # ---------------------------------------------
                # Simulate distance matrix
                # ---------------------------------------------
                D = simulate_distance_matrix(
                    n=n,
                    seed=seed + k,
                    asymmetry_strength=asymmetry_strength,
                    outlier_fraction=outlier_fraction,
                    cluster_strength=cluster_strength,
                )
                R = list(range(n))
                # ---------------------------------------------
                # Exact baseline (reference)
                # ---------------------------------------------
                t0 = time.perf_counter()
                _, L_exact = solve_route(
                    D=D,
                    R=R,
                    strict_order=False,
                    problem_type=problem_type,
                    solver="exact",
                    deterministic=True,
                    fixed_endpoints=fixed_endpoints,
                )
                t1 = time.perf_counter()
                exact_id = _solver_id("exact", True)
                results[problem_type][n][exact_id]["L"].append(L_exact)
                results[problem_type][n][exact_id]["L_exact"].append(L_exact)
                results[problem_type][n][exact_id]["gap"].append(0.0)
                results[problem_type][n][exact_id]["exact_match"].append(True)
                results[problem_type][n][exact_id]["runtime"].append(t1 - t0)
                # ---------------------------------------------
                # Heuristic solvers
                # ---------------------------------------------
                for solver, det_modes in solver_modes.items():
                    if solver == "exact":
                        continue
                    for deterministic in det_modes:
                        sid = _solver_id(solver, deterministic)
                        t0 = time.perf_counter()
                        _, L = solve_route(
                            D=D,
                            R=R,
                            strict_order=False,
                            problem_type=problem_type,
                            solver=solver,
                            deterministic=deterministic,
                            fixed_endpoints=fixed_endpoints,
                        )
                        t1 = time.perf_counter()
                        gap = (L - L_exact) / L_exact
                        results[problem_type][n][sid]["L"].append(L)
                        results[problem_type][n][sid]["L_exact"].append(L_exact)
                        results[problem_type][n][sid]["gap"].append(gap)
                        results[problem_type][n][sid]["exact_match"].append(
                            np.isclose(L, L_exact)
                        )
                        results[problem_type][n][sid]["runtime"].append(t1 - t0)

    return results

def plot_validation_summary(
    results: Dict[str, Dict[int, Dict[str, Any]]],
    *,
    problem_type: str,
    n_values: list[int],
    save_path: str,
    ):
    """
    Plot validation summary for one problem type using a single global legend.

    Top row:
        - Mean relative gap vs n
        - Worst-case relative gap vs n

    Bottom row:
        - Average relative gap (bar)
        - Exact recovery rate (bar)
    """

    # --------------------------------------------------
    # Collect solver IDs (exclude exact baseline)
    # --------------------------------------------------
    solver_ids = [
        sid
        for sid in results[problem_type][n_values[0]].keys()
        if not sid.startswith("exact")
    ]

    # --------------------------------------------------
    # Color map: one color per solver
    # --------------------------------------------------
    cmap = plt.get_cmap("tab10")
    color_map = {
        sid: cmap(i % cmap.N)
        for i, sid in enumerate(solver_ids)
    }

    # --------------------------------------------------
    # Aggregate metrics
    # --------------------------------------------------
    mean_gap = {sid: [] for sid in solver_ids}
    max_gap = {sid: [] for sid in solver_ids}
    exact_rate = {sid: [] for sid in solver_ids}
    for n in n_values:
        for sid in solver_ids:
            gaps = np.asarray(results[problem_type][n][sid]["gap"])
            exact = np.asarray(results[problem_type][n][sid]["exact_match"])
            mean_gap[sid].append(np.mean(gaps))
            max_gap[sid].append(np.max(gaps))
            exact_rate[sid].append(np.mean(exact))

    # --------------------------------------------------
    # Figure layout
    # --------------------------------------------------
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Validation Score: Heuristic vs Exact ({problem_type})",
        fontsize=16,
    )

    # --------------------------------------------------
    # TOP-LEFT: Mean relative gap vs n
    # --------------------------------------------------
    ax = axs[0, 0]
    for sid in solver_ids:
        ax.plot(
            n_values,
            mean_gap[sid],
            marker="o",
            color=color_map[sid],
        )
    ax.set_title("Mean Relative Optimality Gap vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("(L − L*) / L*")
    ax.grid(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # --------------------------------------------------
    # TOP-RIGHT: Worst-case relative gap vs n
    # --------------------------------------------------
    ax = axs[0, 1]
    for sid in solver_ids:
        ax.plot(
            n_values,
            max_gap[sid],
            marker="o",
            color=color_map[sid],
        )
    ax.set_title("Worst-case Relative Gap vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("(L − L*) / L*")
    ax.grid(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # --------------------------------------------------
    # BOTTOM-LEFT: Average relative gap (bars)
    # --------------------------------------------------
    ax = axs[1, 0]
    avg_gap = [np.mean(mean_gap[sid]) for sid in solver_ids]
    bars = ax.bar(
        range(len(solver_ids)),
        avg_gap,
        color=[color_map[sid] for sid in solver_ids],
    )
    ax.set_title("Average Relative Gap Across n")
    ax.set_ylabel("Average (L − L*) / L*")
    ax.set_xticks([])
    ax.grid(axis="y")
    for bar, val in zip(bars, avg_gap):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.2%}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # --------------------------------------------------
    # BOTTOM-RIGHT: Exact recovery rate (bars)
    # --------------------------------------------------
    ax = axs[1, 1]
    avg_exact = [np.mean(exact_rate[sid]) for sid in solver_ids]
    bars = ax.bar(
        range(len(solver_ids)),
        avg_exact,
        color=[color_map[sid] for sid in solver_ids],
    )
    ax.set_title("Exact Recovery Rate")
    ax.set_ylabel("Fraction of instances")
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.grid(axis="y")
    for bar, val in zip(bars, avg_exact):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.1%}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # --------------------------------------------------
    # SINGLE GLOBAL LEGEND
    # --------------------------------------------------
    handles = [
        plt.Line2D(
            [0], [0],
            color=color_map[sid],
            marker="o",
            linestyle="-",
        )
        for sid in solver_ids
    ]
    fig.legend(
        handles,
        solver_ids,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        title="Solver (determinism)",
    )
    plt.tight_layout(rect=[0.05, 0.03, 1, 0.95])
    plt.savefig(save_path, dpi=200)
    plt.close()



def main():
    # --------------------------------------------------
    # Validation configuration
    # --------------------------------------------------
    problem_types = ["TSP", "HPP"]

    # ---------------------------------------------------------
    # Deterministic modes per solver and problem type
    # ---------------------------------------------------------
    DETERMINISTIC_MODES = {
        "TSP": {
            "greedy": [True],
            "python_tsp": [True, False],
            "ortools": [True, False],
            "lkh": [True],
            "exact": [True],  
        },
        "HPP": {
            "greedy": [True],
            "greedy_denn": [True],
            "cheapest_insertion": [True],
            "ortools": [True, False],
            "exact": [True],  
        },
    }
    n_values = list(range(6, 15))  # Keep n small due to exact solver
    n_instances = 10

    # --------------------------------------------------
    # Run validation
    # --------------------------------------------------
    results = validate_exact_vs_heuristic(
        problem_types=problem_types,
        n_values=n_values,
        DETERMINISTIC_MODES=DETERMINISTIC_MODES,
        n_instances=n_instances,
        asymmetry_strength=0.2,
        outlier_fraction=0.0,
        cluster_strength=0.6,
    )

    # --------------------------------------------------
    # Plot validation summaries
    # --------------------------------------------------
    for problem_type in problem_types:
        save_path = (
            f"libraries/simulations/_img/validation/solvers/{problem_type.lower()}/"
            f"validation_exact_vs_heuristic_{problem_type.lower()}.png"
        )
        plot_validation_summary(
            results,
            problem_type=problem_type,
            n_values=n_values,
            save_path=save_path,
        )
        print(f"Saved validation plot: {save_path}")

if __name__ == "__main__":
    main()
