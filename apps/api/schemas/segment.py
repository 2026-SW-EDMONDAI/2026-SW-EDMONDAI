import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SegmentSetOut(BaseModel):
    id: uuid.UUID
    videoId: uuid.UUID
    versionNo: int
    status: str
    source: str
    createdBy: uuid.UUID | None
    notes: str | None
    createdAt: datetime
    updatedAt: datetime

    @classmethod
    def from_orm(cls, ss: Any) -> "SegmentSetOut":
        return cls(
            id=ss.id,
            videoId=ss.video_id,
            versionNo=ss.version_no,
            status=ss.status.value if hasattr(ss.status, "value") else ss.status,
            source=ss.source,
            createdBy=ss.created_by,
            notes=ss.notes,
            createdAt=ss.created_at,
            updatedAt=ss.updated_at,
        )


class SegmentOut(BaseModel):
    id: uuid.UUID
    segmentSetId: uuid.UUID
    seqNo: int
    startMs: int
    endMs: int
    title: str
    topic: str | None
    keyConcepts: list | None
    summary: str | None
    sourceType: str
    createdAt: datetime
    updatedAt: datetime

    @classmethod
    def from_orm(cls, s: Any) -> "SegmentOut":
        return cls(
            id=s.id,
            segmentSetId=s.segment_set_id,
            seqNo=s.seq_no,
            startMs=s.start_ms,
            endMs=s.end_ms,
            title=s.title,
            topic=s.topic,
            keyConcepts=s.key_concepts,
            summary=s.summary,
            sourceType=s.source_type,
            createdAt=s.created_at,
            updatedAt=s.updated_at,
        )


class SegmentUpdateRequest(BaseModel):
    title: str | None = None
    topic: str | None = None
    keyConcepts: list | None = None
    summary: str | None = None


class SegmentSplitRequest(BaseModel):
    splitAtMs: int


class SegmentMergeRequest(BaseModel):
    segmentIds: list[uuid.UUID]


class CloneRequest(BaseModel):
    notes: str | None = None
