from shapely.geometry import Point

from services.osm.app.runtime.index import OSMSnapIndex


class DummyIndex(OSMSnapIndex):
    """
    Minimal stub to access instance methods without loading state.
    """
    def __init__(self):
        pass


def test_classify_side_left():
    idx = DummyIndex()

    entry = Point(0, 0)
    exit_ = Point(10, 0)
    proj = Point(5, 1)   # above line → left

    side = idx._classify_side(entry, exit_, proj)
    assert side == "left"


def test_classify_side_right():
    idx = DummyIndex()

    entry = Point(0, 0)
    exit_ = Point(10, 0)
    proj = Point(5, -1)  # below line → right

    side = idx._classify_side(entry, exit_, proj)
    assert side == "right"


def test_classify_side_center():
    idx = DummyIndex()

    entry = Point(0, 0)
    exit_ = Point(10, 0)
    proj = Point(5, 0)   # exactly on line

    side = idx._classify_side(entry, exit_, proj)
    assert side == "center"
