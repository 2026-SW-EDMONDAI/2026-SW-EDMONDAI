import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------- Video ----------

class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organizationId: uuid.UUID
    title: str
    description: str | None
    status: str
    durationMs: int | None
    sourceType: str
    uploadedBy: uuid.UUID
    analyzedAt: datetime | None
    createdAt: datetime
    updatedAt: datetime

    @classmethod
    def from_orm_video(cls, v: Any) -> "VideoOut":
        return cls(
            id=v.id,
            organizationId=v.organization_id,
            title=v.title,
            description=v.description,
            status=v.status.value if hasattr(v.status, "value") else v.status,
            durationMs=v.duration_ms,
            sourceType=v.source_type,
            uploadedBy=v.uploaded_by,
            analyzedAt=v.analyzed_at,
            createdAt=v.created_at,
            updatedAt=v.updated_at,
        )


class VideoListItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    durationMs: int | None
    analyzedAt: datetime | None
    latestSegmentCount: int = 0


class VideoUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class AnalyzeRequest(BaseModel):
    regenerateSegments: bool = True
    captionSource: str = "default"


# ---------- SignalConfig ----------

class SignalConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    videoId: uuid.UUID
    confidenceCheckEnabled: bool
    quizEnabled: bool
    conceptSelectEnabled: bool
    summaryEnabled: bool
    configJson: dict | None = None

    @classmethod
    def from_orm(cls, sc: Any) -> "SignalConfigOut":
        return cls(
            videoId=sc.video_id,
            confidenceCheckEnabled=sc.confidence_check_enabled,
            quizEnabled=sc.quiz_enabled,
            conceptSelectEnabled=sc.concept_select_enabled,
            summaryEnabled=sc.summary_enabled,
            configJson=sc.config_json,
        )


class SignalConfigUpdateRequest(BaseModel):
    confidenceCheckEnabled: bool | None = None
    quizEnabled: bool | None = None
    conceptSelectEnabled: bool | None = None
    summaryEnabled: bool | None = None


# ---------- Caption ----------

class CaptionCueOut(BaseModel):
    seqNo: int
    startMs: int
    endMs: int
    text: str
