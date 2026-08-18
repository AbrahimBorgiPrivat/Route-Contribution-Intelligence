import tempfile
from pathlib import Path

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    cache_exists,
    _get_cache_file_path,
)


def test_cache_exists_false_then_true():

    with tempfile.TemporaryDirectory() as tmpdir:

        base_path = tmpdir
        label = "TestLabel"
        route_id = 12345

        # ------------------------------------------
        # Initially should not exist
        # ------------------------------------------
        assert cache_exists(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=True,
        ) is False

        # ------------------------------------------
        # Create the cache file manually
        # ------------------------------------------
        path = _get_cache_file_path(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=True,
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

        # ------------------------------------------
        # Now it should exist
        # ------------------------------------------
        assert cache_exists(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=True,
        ) is True


def test_cache_exists_strict_variants():

    with tempfile.TemporaryDirectory() as tmpdir:

        base_path = tmpdir
        label = "TestLabel"
        route_id = 42

        # Create only strict=False file
        path_false = _get_cache_file_path(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=False,
        )
        path_false.parent.mkdir(parents=True, exist_ok=True)
        path_false.touch()

        assert cache_exists(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=False,
        ) is True

        assert cache_exists(
            base_path=base_path,
            label=label,
            route_id=route_id,
            strict=True,
        ) is False


if __name__ == "__main__":
    test_cache_exists_false_then_true()
    test_cache_exists_strict_variants()
