import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import OrgContext, require_operator, require_analyst
from schemas.response import Meta, SuccessResponse
from schemas.video import (
    AnalyzeRequest,
    SignalConfigOut,
    SignalConfigUpdateRequest,
    VideoListItem,
    VideoOut,
    VideoUpdateRequest,
)
from services.video_service import VideoService

router = APIRouter(prefix="/api/v1/orgs/{orgId}", tags=["videos"])


def _meta(request_id: str | None = None) -> Meta:
    from fastapi import Request
    return Meta(
        requestId=request_id or str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------- Video CRUD ----------

@router.get("/videos", dependencies=[Depends(require_analyst)])
def list_videos(
    orgId: OrgContext,
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    svc = VideoService(db)
    videos, total = svc.list_videos(orgId, status=status, search=search, page=page, page_size=pageSize)
    items = [
        VideoListItem(
            id=v.id,
            title=v.title,
            status=v.status.value if hasattr(v.status, "value") else v.status,
            durationMs=v.duration_ms,
            analyzedAt=v.analyzed_at,
        )
        for v in videos
    ]
    return {
        "data": [i.model_dump() for i in items],
        "meta": {
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.post("/videos", status_code=201, dependencies=[Depends(require_operator)])
def create_video(
    orgId: OrgContext,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str | None = Form(None),
    sourceType: str = Form("upload"),
    confidenceCheckEnabled: bool = Form(True),
    quizEnabled: bool = Form(False),
    conceptSelectEnabled: bool = Form(False),
    summaryEnabled: bool = Form(False),
    videoFile: UploadFile | None = File(None),
    subtitleFile: UploadFile | None = File(None),
    # current user injected via require_operator
    user: dict = Depends(require_operator),
):
    svc = VideoService(db)
    video, signal_config = svc.create_video(
        org_id=orgId,
        uploaded_by=uuid.UUID(user["sub"]),
        title=title,
        description=description,
        source_type=sourceType,
        video_file=videoFile,
        subtitle_file=subtitleFile,
        confidence_check_enabled=confidenceCheckEnabled,
        quiz_enabled=quizEnabled,
        concept_select_enabled=conceptSelectEnabled,
        summary_enabled=summaryEnabled,
    )
    return {
        "data": {
            "video": VideoOut.from_orm_video(video).model_dump(),
            "signalConfig": SignalConfigOut.from_orm(signal_config).model_dump(),
        },
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/videos/{videoId}", dependencies=[Depends(require_analyst)])
def get_video(
    orgId: OrgContext,
    videoId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = VideoService(db)
    video = svc.get_video(orgId, videoId)
    return {
        "data": {"video": VideoOut.from_orm_video(video).model_dump()},
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.patch("/videos/{videoId}", dependencies=[Depends(require_operator)])
def update_video(
    orgId: OrgContext,
    videoId: uuid.UUID,
    body: VideoUpdateRequest,
    db: Session = Depends(get_db),
):
    svc = VideoService(db)
    video = svc.update_video(orgId, videoId, body.title, body.description)
    return {
        "data": VideoOut.from_orm_video(video).model_dump(),
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.post("/videos/{videoId}/analyze", status_code=202, dependencies=[Depends(require_operator)])
def analyze_video(
    orgId: OrgContext,
    videoId: uuid.UUID,
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    svc = VideoService(db)
    svc.trigger_analyze(orgId, videoId)
    return {
        "data": {
            "videoId": str(videoId),
            "status": "processing",
            "message": "Analysis job accepted.",
        },
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------- Signal Config ----------

@router.get("/videos/{videoId}/signal-config", dependencies=[Depends(require_analyst)])
def get_signal_config(
    orgId: OrgContext,
    videoId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = VideoService(db)
    config = svc.get_signal_config(orgId, videoId)
    return {
        "data": SignalConfigOut.from_orm(config).model_dump(),
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.patch("/videos/{videoId}/signal-config", dependencies=[Depends(require_operator)])
def update_signal_config(
    orgId: OrgContext,
    videoId: uuid.UUID,
    body: SignalConfigUpdateRequest,
    db: Session = Depends(get_db),
):
    svc = VideoService(db)
    config = svc.update_signal_config(
        orgId,
        videoId,
        body.confidenceCheckEnabled,
        body.quizEnabled,
        body.conceptSelectEnabled,
        body.summaryEnabled,
    )
    return {
        "data": SignalConfigOut.from_orm(config).model_dump(),
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
