from pathlib import Path

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _get_cache_file_path,
)

def test_get_cache_file_path_type1():
    base_path = "/project_root"
    label = "unstructured_all"
    route_id = 123
    strict = True
    path = _get_cache_file_path(
        base_path=base_path,
        label=label,
        route_id=route_id,
        strict=strict,
    )
    expected = Path("/project_root/data/unstructured_all/123/c_distances_type1.json")
    assert path == expected
    assert path.name == "c_distances_type1.json"


def test_get_cache_file_path_type2():
    base_path = "/project_root"
    label = "structured_revenue"
    route_id = "456"
    strict = False
    path = _get_cache_file_path(
        base_path=base_path,
        label=label,
        route_id=route_id,
        strict=strict,
    )
    expected = Path("/project_root/data/structured_revenue/456/c_distances_type2.json")
    assert path == expected
    assert path.name == "c_distances_type2.json"

if __name__ == "__main__":
    test_get_cache_file_path_type1()
    test_get_cache_file_path_type2()
