import numpy as np
import pytest

from libraries.utils.visualization.geojson_pipeline import _get_E_value


def test_get_E_value_scalar_int():
    E = 5
    assert _get_E_value(E, 0) == 5.0
    assert _get_E_value(E, 10) == 5.0


def test_get_E_value_scalar_float():
    E = 3.14
    assert _get_E_value(E, 0) == 3.14
    assert _get_E_value(E, 99) == 3.14


def test_get_E_value_list():
    E = [1.0, 2.5, 4.0]
    assert _get_E_value(E, 0) == 1.0
    assert _get_E_value(E, 1) == 2.5
    assert _get_E_value(E, 2) == 4.0


def test_get_E_value_list_index_error():
    E = [1.0, 2.0]
    with pytest.raises(IndexError):
        _get_E_value(E, 2)


def test_get_E_value_numpy_1d():
    E = np.array([10.0, 20.0, 30.0])
    assert _get_E_value(E, 0) == 10.0
    assert _get_E_value(E, 1) == 20.0
    assert _get_E_value(E, 2) == 30.0


def test_get_E_value_numpy_2d():
    E = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert _get_E_value(E, 0) == 1.0
    assert _get_E_value(E, 1) == 2.0
    assert _get_E_value(E, 2) == 3.0
    assert _get_E_value(E, 3) == 4.0


def test_get_E_value_numpy_2d_index_error():
    E = np.array([[1.0, 2.0], [3.0, 4.0]])
    with pytest.raises(IndexError):
        _get_E_value(E, 4)
