from __future__ import annotations
from typing import Dict, Tuple

"""
Golden dataset integration tests.
"""

# --------------------------------------------------
# Golden points (Bornholm)
# --------------------------------------------------
GOLDEN_POINTS: Dict[str, Tuple[float, float]] = {
    "bornholm_1": (863994, 6123307),
    "bornholm_2": (863973, 6123314),
    "bornholm_3": (863956, 6123159),
    "bornholm_4": (863948, 6123008),
    "bornholm_5": (863979, 6123224),
}

def test_golden_snap_nearest(snap_index):
    """
    Golden dataset test for snap_nearest.
    """
    results = {}
    for name, (x, y) in GOLDEN_POINTS.items():
        res = snap_index.snap_nearest(
            x=x,
            y=y,
            input_crs="EPSG:25832",
            output_crs="EPSG:4326",
            allowed_highways={
                "secondary",
                "primary",
                "motorway",
            },
        )
        segment = res["segment"]
        geom = res["geometry"]
        results[name] = {
            "entry_node": segment["entry_node"],
            "exit_node": segment["exit_node"],
            "side_of_road": geom["side_of_road"],
        }
    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    for name, r in results.items():
        assert r["entry_node"] != r["exit_node"], f"{name}: degenerate segment"
        assert r["side_of_road"] in {"left", "right", "center"}, f"{name}: invalid side"

    # --------------------------------------------------
    # Golden lock (explicit expectations)
    # --------------------------------------------------
    assert results == {'bornholm_1': {'entry_node': 502254929,
                                        'exit_node': 9346460737,
                                        'side_of_road': 'right'},
                        'bornholm_2': {'entry_node': 502254929,
                                        'exit_node': 9346460737,
                                        'side_of_road': 'right'},
                        'bornholm_3': {'entry_node': 1184372201,
                                        'exit_node': 12228720723,
                                        'side_of_road': 'right'},
                        'bornholm_4': {'entry_node': 3013950063,
                                        'exit_node': 12228720405,
                                        'side_of_road': 'left'},
                        'bornholm_5': {'entry_node': 12228720723,
                                        'exit_node': 4790151725,
                                        'side_of_road': 'left'}}
    