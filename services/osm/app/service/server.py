from __future__ import annotations

import logging
from typing import Optional, Set, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.runtime.index import OSMSnapIndex
from app.service.dependencies import get_snap_index

router = APIRouter()

# ==================================================
# Request models
# ==================================================

class SnapNearestRequest(BaseModel):
    """
    Request model for nearest-segment snapping (single point).
    """
    x: float = Field(..., description="X coordinate (lon / easting)")
    y: float = Field(..., description="Y coordinate (lat / northing)")
    input_crs: str = Field(
        default="EPSG:4326",
        description="CRS of input coordinates",
    )
    output_crs: Optional[str] = Field(
        default=None,
        description="Desired output CRS (defaults to metric CRS)",
    )
    allowed_highways: Optional[Set[str]] = Field(
        default=None,
        description="Restrict snapping to these highway types",
    )

class SnapNearestBatchRequest(BaseModel):
    """
    Request model for batch nearest-segment snapping.
    """
    points: List[List[float]] = Field(
        ...,
        description="List of [x, y] coordinate pairs",
        example=[[863994, 6123307], [863973, 6123314]],
    )
    input_crs: str = Field(
        default="EPSG:4326",
        description="CRS of input coordinates",
    )
    output_crs: Optional[str] = Field(
        default=None,
        description="Desired output CRS (defaults to metric CRS)",
    )
    allowed_highways: Optional[Set[str]] = Field(
        default=None,
        description="Restrict snapping to these highway types",
    )
    strict: bool = Field(
        default=True,
        description="If true, fail on first error; otherwise return partial results",
    )

# ==================================================
# Response models
# ==================================================

class TurnResponse(BaseModel):
    turn_id: int
    from_segment: int
    to_segment: int
    node: int
    angle_deg: float
    from_osmid: int
    to_osmid: int
    from_highway: Optional[str]
    to_highway: Optional[str]

class GeometryPointResponse(BaseModel):
    x: float
    y: float
    node_id: int
    turns: Optional[List[TurnResponse]] = None

class TangentVectorResponse(BaseModel):
    tangent: Optional[List[float]] = None
    tangent_hat: Optional[List[float]] = None


class SegmentVectorsResponse(BaseModel):
    entry: TangentVectorResponse
    exit: TangentVectorResponse

class GeometryResponse(BaseModel):
    entry_point: GeometryPointResponse
    exit_point: GeometryPointResponse
    side_of_road: Optional[str] = None
    vectors: Optional[SegmentVectorsResponse] = None
    crs: str
    
class SnapNearestResponse(BaseModel):
    input: dict
    segment: dict
    projected_point: dict
    geometry: GeometryResponse

class SnapNearestBatchResponse(BaseModel):
    results: List[SnapNearestResponse]

class SegmentResponse(BaseModel):
    segment: dict
    geometry: GeometryResponse

# ==================================================
# Routes
# ==================================================

@router.get("/health")
def health() -> dict[str, str]:
    """
    Health check.
    """
    return {"status": "ok"}

@router.post(
    "/snap/nearest",
    response_model=SnapNearestResponse,
)
def snap_nearest(
    req: SnapNearestRequest,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Snap a single point to the nearest junction-bounded road segment.

    - No turn traversal
    - No road extension
    """
    logging.info("API snap_nearest called")
    return snap_index.snap_nearest(
        x=req.x,
        y=req.y,
        input_crs=req.input_crs,
        output_crs=req.output_crs,
        allowed_highways=req.allowed_highways,
    )

@router.post(
    "/snap/nearest/batch",
    response_model=SnapNearestBatchResponse,
)
def snap_nearest_batch(
    req: SnapNearestBatchRequest,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Snap multiple points to their nearest junction-bounded road segments.

    Returns one result per input point, in the same order.
    """
    logging.info("API snap_nearest_batch called (%d points)", len(req.points))
    results = snap_index.snap_nearest_batch(
        points=req.points,
        input_crs=req.input_crs,
        output_crs=req.output_crs,
        allowed_highways=req.allowed_highways,
        strict=req.strict,
    )
    return {"results": results}

@router.get(
    "/segments/{segment_id}",
    response_model=SegmentResponse,
)
def get_segment(
    segment_id: int,
    output_crs: Optional[str] = None,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Return metadata and geometry for a single segment.
    """
    logging.info("API get_segment called (segment_id=%s)", segment_id)
    return snap_index.get_segment(
        segment_id=segment_id,
        output_crs=output_crs,
    )

@router.get(
    "/turns/{turn_id}",
    response_model=Optional[TurnResponse],
)
def get_turn(
    turn_id: int,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Return a single turn by turn_id.
    """
    logging.info("API get_turn called (turn_id=%s)", turn_id)
    return snap_index.get_turn(turn_id)

@router.get(
    "/segments/{segment_id}/turns",
    response_model=List[TurnResponse],
)
def get_turns_from_segment(
    segment_id: int,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Return all outgoing turns from a segment.
    """
    logging.info("API get_turns_from_segment called (segment_id=%s)", segment_id)
    return snap_index.get_turns_from_segment(segment_id)

@router.get(
    "/nodes/{node_id}/turns",
    response_model=List[TurnResponse],
)
def get_turns_from_node(
    node_id: int,
    snap_index: OSMSnapIndex = Depends(get_snap_index),
):
    """
    Return all turns that occur at a node.
    """
    logging.info("API get_turns_from_node called (node_id=%s)", node_id)
    return snap_index.get_turns_from_node(node_id)
