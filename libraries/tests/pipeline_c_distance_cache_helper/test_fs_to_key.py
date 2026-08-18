from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import _fs_to_key

def test_fs_to_key():
    assert _fs_to_key(frozenset()) == ""
    assert _fs_to_key(frozenset({1})) == "1"
    assert _fs_to_key(frozenset({2, 1})) == "1;2"
    assert _fs_to_key(frozenset({5, 3, 9})) == "3;5;9"

if __name__ == "__main__":
    test_fs_to_key()