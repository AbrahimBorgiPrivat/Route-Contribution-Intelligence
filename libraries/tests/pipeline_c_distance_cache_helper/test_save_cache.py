import json
import tempfile

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    save_cache,
    _get_cache_file_path,
)

def test_save_cache_type1():
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = tmp_dir
        label = "label_a"
        route_id = 99
        strict = True
        C_distance_full = {
            frozenset(): 0.0,
            frozenset({2, 1}): 7.25,
        }
        R_seq = [0, 1, 2]
        L_R = 42.5
        save_cache(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
            C_distance_full=C_distance_full,
            R_seq=R_seq,
            L_R=L_R,
        )
        path = _get_cache_file_path(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
        )
        assert path.exists()
        assert path.name == "c_distances_type1.json"
        with open(path, "r") as f:
            raw = json.load(f)
        assert "C_distance_full" in raw
        assert "R_seq" in raw
        assert "L_R" in raw
        assert raw["C_distance_full"][""] == 0.0
        assert raw["C_distance_full"]["1;2"] == 7.25
        assert raw["R_seq"] == R_seq
        assert raw["L_R"] == L_R


def test_save_cache_type2():
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = tmp_dir
        label = "label_b"
        route_id = "abc"
        strict = False
        save_cache(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
            C_distance_full={frozenset({5}): 4.5},
            R_seq=[5],
            L_R=10.0,
        )
        path = _get_cache_file_path(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
        )
        assert path.exists()
        assert path.name == "c_distances_type2.json"
        with open(path, "r") as f:
            raw = json.load(f)
        assert raw["C_distance_full"]["5"] == 4.5

if __name__ == "__main__":
    test_save_cache_type1()
    test_save_cache_type2()
