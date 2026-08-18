import base64
import pickle
import numpy as np

from libraries.utils.pipelines.c_algorithm_layer.v2.pipeline_c_distance_cache_helper import (
    _unb64_pickle,
)

def test_unb64_pickle_basic_object():
    original = {"a": 1, "b": [1, 2, 3]}
    encoded = base64.b64encode(
        pickle.dumps(original, protocol=pickle.HIGHEST_PROTOCOL)
    ).decode("ascii")
    decoded = _unb64_pickle(encoded)
    assert decoded == original

def test_unb64_pickle_numpy_array():
    arr = np.array([[10, 20], [30, 40]])
    encoded = base64.b64encode(
        pickle.dumps(arr, protocol=pickle.HIGHEST_PROTOCOL)
    ).decode("ascii")
    decoded = _unb64_pickle(encoded)
    assert isinstance(decoded, np.ndarray)
    assert np.array_equal(decoded, arr)

def test_unb64_pickle_complex_structure():
    original = {
        "matrix": np.arange(4).reshape(2, 2),
        "nested": {"x": {1, 2, 3}},
        "value": 3.14,
    }
    encoded = base64.b64encode(
        pickle.dumps(original, protocol=pickle.HIGHEST_PROTOCOL)
    ).decode("ascii")
    decoded = _unb64_pickle(encoded)
    assert np.array_equal(decoded["matrix"], original["matrix"])
    assert decoded["nested"]["x"] == {1, 2, 3}
    assert decoded["value"] == 3.14


if __name__ == "__main__":
    test_unb64_pickle_basic_object()
    test_unb64_pickle_numpy_array()
    test_unb64_pickle_complex_structure()
