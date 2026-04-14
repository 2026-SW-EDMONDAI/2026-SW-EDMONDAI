from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "meta": {
                "requestId": getattr(request.state, "request_id", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
            "meta": {
                "requestId": getattr(request.state, "request_id", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
