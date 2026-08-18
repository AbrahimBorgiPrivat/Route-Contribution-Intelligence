from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import _key_to_fs

def test_key_to_fs():
    assert _key_to_fs("") == frozenset()
    assert _key_to_fs("1") == frozenset({1})
    assert _key_to_fs("1;2") == frozenset({1, 2})
    assert _key_to_fs("3;5;9") == frozenset({3, 5, 9})

if __name__ == "__main__":
    test_key_to_fs()