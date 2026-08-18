from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _deserialize_fs_dict,
)

def test_deserialize_fs_dict():
    input_dict = {
        "": 1.0,
        "1;2": 3.5,
        "5": 7.0,
    }
    result = _deserialize_fs_dict(input_dict)
    assert result[frozenset()] == 1.0
    assert result[frozenset({1, 2})] == 3.5
    assert result[frozenset({5})] == 7.0
    assert len(result) == 3

if __name__ == "__main__":
    test_deserialize_fs_dict()