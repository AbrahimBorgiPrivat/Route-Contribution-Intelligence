import numpy as np

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _b64_pickle,
    _unb64_pickle,
)

def test_b64_pickle_basic_types():
    obj = {
        "a": 1,
        "b": 2.5,
        "c": [1, 2, 3],
        "d": {"x": 10},
    }
    encoded = _b64_pickle(obj)
    decoded = _unb64_pickle(encoded)
    assert decoded == obj


def test_b64_pickle_numpy_array():
    arr = np.array([[1, 2], [3, 4]], dtype=float)
    encoded = _b64_pickle(arr)
    decoded = _unb64_pickle(encoded)
    assert isinstance(decoded, np.ndarray)
    assert np.array_equal(decoded, arr)

def test_b64_pickle_complex_structure():
    complex_obj = {
        "matrix": np.arange(9).reshape(3, 3),
        "inner": {
            "list": [1, 2, 3],
            "set": {4, 5},
        },
        "value": 42.0,
    }
    encoded = _b64_pickle(complex_obj)
    decoded = _unb64_pickle(encoded)
    assert isinstance(decoded["matrix"], np.ndarray)
    assert np.array_equal(decoded["matrix"], complex_obj["matrix"])
    assert decoded["inner"]["list"] == [1, 2, 3]
    assert decoded["inner"]["set"] == {4, 5}
    assert decoded["value"] == 42.0

if __name__ == "__main__":
    test_b64_pickle_basic_types()
    test_b64_pickle_numpy_array()
    test_b64_pickle_complex_structure()
