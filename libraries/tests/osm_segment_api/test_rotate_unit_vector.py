import math
from libraries.classes.osm_segment_api import rotate_unit_vector

def almost_equal(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) < eps

def assert_vec_close(v1, v2, eps: float = 1e-9):
    assert almost_equal(v1[0], v2[0], eps), f"x mismatch: {v1[0]} != {v2[0]}"
    assert almost_equal(v1[1], v2[1], eps), f"y mismatch: {v1[1]} != {v2[1]}"

def test_rotate_zero_degrees_identity():
    """
    Rotating by 0° should return the original vector.
    """
    v = (1.0, 0.0)
    r = rotate_unit_vector(v, 0.0)
    assert_vec_close(r, v)

def test_rotate_90_degrees_ccw():
    """
    +90° rotation (CCW) of (1, 0) should be (0, 1).
    """
    v = (1.0, 0.0)
    r = rotate_unit_vector(v, 90.0)
    assert_vec_close(r, (0.0, 1.0))

def test_rotate_minus_90_degrees_cw():
    """
    -90° rotation (CW) of (1, 0) should be (0, -1).
    """
    v = (1.0, 0.0)
    r = rotate_unit_vector(v, -90.0)
    assert_vec_close(r, (0.0, -1.0))

def test_rotate_180_degrees():
    """
    180° rotation should invert the vector.
    """
    v = (0.6, -0.8)
    r = rotate_unit_vector(v, 180.0)
    assert_vec_close(r, (-0.6, 0.8))


def test_rotate_preserves_unit_length():
    """
    Rotation must preserve vector magnitude.
    """
    v = (math.sqrt(0.5), math.sqrt(0.5))  
    r = rotate_unit_vector(v, 37.0)
    norm = math.hypot(r[0], r[1])
    assert almost_equal(norm, 1.0), f"length changed: {norm}"


def test_rotation_composition():
    """
    Rotating by a then b should equal rotating by (a + b).
    """
    v = (1.0, 0.0)
    r1 = rotate_unit_vector(v, 30.0)
    r2 = rotate_unit_vector(r1, 60.0)
    r_direct = rotate_unit_vector(v, 90.0)
    assert_vec_close(r2, r_direct)


def test_rotation_of_non_axis_aligned_vector():
    """
    General sanity test on arbitrary unit vector.
    """
    v = (0.6, 0.8)  
    r = rotate_unit_vector(v, 90.0)
    expected = (-0.8, 0.6)
    assert_vec_close(r, expected)


if __name__ == "__main__":
    test_rotate_zero_degrees_identity()
    test_rotate_90_degrees_ccw()
    test_rotate_minus_90_degrees_cw()
    test_rotate_180_degrees()
    test_rotate_preserves_unit_length()
    test_rotation_composition()
    test_rotation_of_non_axis_aligned_vector()
