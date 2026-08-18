from shapely.geometry import Point

def test_projected_point_on_segment(snap_index):
    res = snap_index.snap_nearest(
        x=863994,
        y=6123307,
        input_crs="EPSG:25832",
        output_crs=None,  
    )
    sid = res["segment"]["segment_id"]
    geom = snap_index.state.geom_by_segment_id[sid]
    proj = Point(
        res["projected_point"]["x"],
        res["projected_point"]["y"],
    )
    assert geom.distance(proj) < 1e-6
