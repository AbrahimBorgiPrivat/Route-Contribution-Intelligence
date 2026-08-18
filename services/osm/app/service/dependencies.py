from fastapi import Request

from app.runtime.index import OSMSnapIndex


def get_snap_index(request: Request) -> OSMSnapIndex:
    """
    FastAPI dependency that returns the snap index instance
    loaded at application startup.
    """
    snap_index = getattr(request.app.state, "snap_index", None)
    if snap_index is None:
        raise RuntimeError("Snap index not initialized")
    return snap_index
