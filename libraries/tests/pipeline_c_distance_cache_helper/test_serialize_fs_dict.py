from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _serialize_fs_dict,
)

def test_serialize_fs_dict():
    input_dict = {
        frozenset(): 1.0,
        frozenset({2, 1}): 3.5,
        frozenset({5}): 7,
    }
    result = _serialize_fs_dict(input_dict)
    assert result[""] == 1.0
    assert result["1;2"] == 3.5
    assert result["5"] == 7.0
    assert len(result) == 3

if __name__ == "__main__":
    test_serialize_fs_dict()