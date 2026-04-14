from fastapi import APIRouter, Request

from schemas.response import Meta, SuccessResponse
from core.config import settings

router = APIRouter(tags=["System"])


@router.get("/health", response_model=SuccessResponse)
async def health(request: Request) -> SuccessResponse:
    return SuccessResponse(
        data={"status": "ok"},
        meta=Meta(requestId=request.state.request_id),
    )


@router.get("/version", response_model=SuccessResponse)
async def version(request: Request) -> SuccessResponse:
    return SuccessResponse(
        data={"version": settings.APP_VERSION},
        meta=Meta(requestId=request.state.request_id),
    )
