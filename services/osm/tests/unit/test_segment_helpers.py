from shapely.geometry import LineString

from services.osm.app.runtime.index import OSMSnapIndex
from services.osm.app.runtime.types import SnapIndexState


def test_get_segment_geometry_basic():
    # Fake state
    geom = LineString([(0, 0), (10, 0)])

    state = SnapIndexState(
        metric_crs="EPSG:3857",
        geom_by_segment_id={1: geom},
        meta_by_segment_id={
            1: {
                "segment_id": 1,
                "osmid": 100,
                "highway": "residential",
                "name": None,
                "entry_node": 10,
                "exit_node": 11,
            }
        },
        segment_id_by_row_index=[1],
        row_index_by_highway={},
        trees={},
        turns_by_from_segment={},
        turns={},
    )

    idx = OSMSnapIndex(state)

    seg = idx.get_segment(segment_id=1, output_crs="EPSG:3857")

    assert seg["segment"]["segment_id"] == 1
    assert seg["geometry"]["entry_point"]["node_id"] == 10
    assert seg["geometry"]["exit_point"]["node_id"] == 11
