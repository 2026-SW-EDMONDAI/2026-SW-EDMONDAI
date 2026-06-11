import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import OrgContext, require_analyst, require_operator
from schemas.segment import (
    CloneRequest,
    SegmentMergeRequest,
    SegmentOut,
    SegmentSetOut,
    SegmentSplitRequest,
    SegmentUpdateRequest,
)
from services.segment_service import SegmentService

router = APIRouter(prefix="/api/v1/orgs/{orgId}", tags=["segments"])


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Segment Sets ----------

@router.get("/videos/{videoId}/segment-sets", dependencies=[Depends(require_analyst)])
def list_segment_sets(
    orgId: OrgContext,
    videoId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = SegmentService(db)
    sets = svc.list_sets(videoId)
    return {
        "data": [SegmentSetOut.from_orm(ss).model_dump() for ss in sets],
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.get("/videos/{videoId}/segment-sets/latest", dependencies=[Depends(require_analyst)])
def get_latest_segment_set(
    orgId: OrgContext,
    videoId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = SegmentService(db)
    ss = svc.get_latest_set(videoId)
    return {
        "data": SegmentSetOut.from_orm(ss).model_dump(),
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.post("/videos/{videoId}/segment-sets/{segmentSetId}/clone", status_code=201)
def clone_segment_set(
    orgId: OrgContext,
    videoId: uuid.UUID,
    segmentSetId: uuid.UUID,
    body: CloneRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_operator),
):
    svc = SegmentService(db)
    new_set = svc.clone_set(videoId, segmentSetId, uuid.UUID(user["sub"]), body.notes)
    return {
        "data": SegmentSetOut.from_orm(new_set).model_dump(),
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.post("/videos/{videoId}/segment-sets/{segmentSetId}/finalize", dependencies=[Depends(require_operator)])
def finalize_segment_set(
    orgId: OrgContext,
    videoId: uuid.UUID,
    segmentSetId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = SegmentService(db)
    ss = svc.finalize_set(videoId, segmentSetId)
    return {
        "data": {
            "segmentSetId": str(ss.id),
            "status": ss.status.value,
            "finalizedAt": _ts(),
        },
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


# ---------- Segments ----------

@router.get("/segment-sets/{segmentSetId}/segments", dependencies=[Depends(require_analyst)])
def list_segments(
    orgId: OrgContext,
    segmentSetId: uuid.UUID,
    db: Session = Depends(get_db),
):
    svc = SegmentService(db)
    segments = svc.list_segments(segmentSetId)
    return {
        "data": [SegmentOut.from_orm(s).model_dump() for s in segments],
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.patch("/segment-sets/{segmentSetId}/segments/{segmentId}", dependencies=[Depends(require_operator)])
def update_segment(
    orgId: OrgContext,
    segmentSetId: uuid.UUID,
    segmentId: uuid.UUID,
    body: SegmentUpdateRequest,
    db: Session = Depends(get_db),
    videoId: uuid.UUID | None = None,
):
    # Resolve videoId from segmentSet
    from sqlalchemy import select
    from models.segment import SegmentSet
    ss = db.scalar(select(SegmentSet).where(SegmentSet.id == segmentSetId))
    if not ss:
        from core.exceptions import AppException
        raise AppException(code="NOT_FOUND", message="Segment set not found.", status_code=404)

    svc = SegmentService(db)
    seg = svc.update_segment(ss.video_id, segmentSetId, segmentId, body.title, body.topic, body.keyConcepts, body.summary)
    return {
        "data": SegmentOut.from_orm(seg).model_dump(),
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.post("/segment-sets/{segmentSetId}/segments/{segmentId}/split", status_code=201, dependencies=[Depends(require_operator)])
def split_segment(
    orgId: OrgContext,
    segmentSetId: uuid.UUID,
    segmentId: uuid.UUID,
    body: SegmentSplitRequest,
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from models.segment import SegmentSet
    ss = db.scalar(select(SegmentSet).where(SegmentSet.id == segmentSetId))
    if not ss:
        from core.exceptions import AppException
        raise AppException(code="NOT_FOUND", message="Segment set not found.", status_code=404)

    svc = SegmentService(db)
    first, second = svc.split_segment(ss.video_id, segmentSetId, segmentId, body.splitAtMs)
    return {
        "data": {
            "originalSegmentId": str(segmentId),
            "newSegments": [
                SegmentOut.from_orm(first).model_dump(),
                SegmentOut.from_orm(second).model_dump(),
            ],
        },
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }


@router.post("/segment-sets/{segmentSetId}/segments/merge", status_code=201, dependencies=[Depends(require_operator)])
def merge_segments(
    orgId: OrgContext,
    segmentSetId: uuid.UUID,
    body: SegmentMergeRequest,
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from models.segment import SegmentSet
    ss = db.scalar(select(SegmentSet).where(SegmentSet.id == segmentSetId))
    if not ss:
        from core.exceptions import AppException
        raise AppException(code="NOT_FOUND", message="Segment set not found.", status_code=404)

    svc = SegmentService(db)
    merged = svc.merge_segments(ss.video_id, segmentSetId, body.segmentIds)
    return {
        "data": {"mergedSegment": SegmentOut.from_orm(merged).model_dump()},
        "meta": {"requestId": str(uuid.uuid4()), "timestamp": _ts()},
    }
