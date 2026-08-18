import pandas as pd
import numpy as np
from pathlib import Path

def make_small_routes_from_real(
    src_csv: str,
    dst_csv: str,
    *,
    n_routes: int = 30,
    n_per_route: int = 10,
    n_outliers: int = 2,
    seed: int = 42,
    ) -> None:
    """
    Create a small real-route dataset:
      - Select n_routes distinct route IDs
      - For each route, select n_per_route addresses
      - Force n_outliers peripheral rows per route
    """
    rng = np.random.default_rng(seed)
    df = pd.read_csv(src_csv, sep=";", dtype=str)
    if "id" not in df.columns:
        raise ValueError("CSV must contain an 'id' column")
    route_ids = df["id"].unique()
    if len(route_ids) < n_routes:
        raise ValueError(
            f"Only {len(route_ids)} unique routes available, "
            f"but {n_routes} requested"
        )
    chosen_ids = rng.choice(route_ids, size=n_routes, replace=False)
    rows = []
    for rid in chosen_ids:
        df_r = df[df["id"] == rid]
        if len(df_r) < n_per_route:
            continue
        core = df_r.sample(
            n=n_per_route - n_outliers,
            random_state=int(rng.integers(0, 1e9))
        )
        candidates = df_r.drop(core.index)
        k1 = n_outliers // 2 + n_outliers % 2
        k2 = n_outliers // 2
        outliers = pd.concat([
            candidates.head(k1),
            candidates.tail(k2),
        ])
        subset = pd.concat([core, outliers], ignore_index=True)
        subset = subset.sample(
            frac=1.0,
            random_state=int(rng.integers(0, 1e9))
        )
        rows.append(subset)
    small = pd.concat(rows, ignore_index=True)
    Path(dst_csv).parent.mkdir(parents=True, exist_ok=True)
    small.to_csv(dst_csv, sep=";", index=False)
    print(f"Written {dst_csv}")
    print(f"Routes: {small['id'].nunique()}")
    print(f"Rows:   {len(small)}")


if __name__ == "__main__":
    make_small_routes_from_real(
        src_csv="libraries/simulations/_data/routes/tsp_simulationdata.csv",
        dst_csv="libraries/simulations/_data/routes/tsp_small_30x10.csv",
        seed=123,
    )

    make_small_routes_from_real(
        src_csv="libraries/simulations/_data/routes/hpp_simulationdata.csv",
        dst_csv="libraries/simulations/_data/routes/hpp_small_30x10.csv",
        seed=456,
    )
