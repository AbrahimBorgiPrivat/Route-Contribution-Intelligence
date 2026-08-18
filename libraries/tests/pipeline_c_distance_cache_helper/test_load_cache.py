import json
import tempfile

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    load_cache,
    _get_cache_file_path,
)

def test_load_cache():
    # ----------------------------------------
    # Create temporary directory structure
    # ----------------------------------------
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = tmp_dir
        label = "test_label"
        route_id = 42
        strict = True
        cache_path = _get_cache_file_path(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # ----------------------------------------
        # Create mock cache file content
        # ----------------------------------------
        mock_payload = {
            "C_distance_full": {
                "": 0.0,
                "1;2": 7.25,
            },
            "R_seq": [0, 1, 2, 3],
            "L_R": 123.45,
        }
        with open(cache_path, "w") as f:
            json.dump(mock_payload, f)

        # ----------------------------------------
        # Load cache
        # ----------------------------------------
        result = load_cache(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=strict,
        )

        # ----------------------------------------
        # Assertions
        # ----------------------------------------
        assert "C_distance_full" in result
        assert "R_seq" in result
        assert "L_R" in result
        assert result["C_distance_full"][frozenset()] == 0.0
        assert result["C_distance_full"][frozenset({1, 2})] == 7.25
        assert result["R_seq"] == [0, 1, 2, 3]
        assert result["L_R"] == 123.45

if __name__ == "__main__":
    test_load_cache()
