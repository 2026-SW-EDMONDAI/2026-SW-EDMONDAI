from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Meta(BaseModel):
    requestId: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SuccessResponse(BaseModel):
    data: Any
    meta: Meta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
    meta: Meta
