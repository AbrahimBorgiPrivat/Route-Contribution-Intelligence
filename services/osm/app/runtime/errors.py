from fastapi import Request
from fastapi.responses import JSONResponse

def register_osm_error_handlers(app):
    @app.exception_handler(OSMServiceError)
    async def osm_service_error_handler(request: Request, exc: OSMServiceError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "hint": exc.hint,
                "endpoint": request.url.path,
            },
        )
    
class OSMServiceError(Exception):
    """
    Base class for all expected domain errors in the OSM service.
    These errors are safe to expose to clients.
    """
    status_code: int = 400
    def __init__(self, message: str, *, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(message)

class NoSegmentFoundError(OSMServiceError):
    status_code = 400
    def __init__(self, *, hint: str | None = None):
        super().__init__(
            "No segment found for given coordinates and filters.",
            hint=hint,
        )


class InvalidCRSError(OSMServiceError):
    status_code = 422
    def __init__(self, crs: str):
        super().__init__(
            f"Invalid or unsupported CRS: {crs}",
            hint="Check input_crs parameter.",
        )

class InvalidHighwayFilterError(OSMServiceError):
    status_code = 422
    def __init__(self, highways):
        super().__init__(
            "Invalid highway filter.",
            hint=f"Received: {highways}",
        )