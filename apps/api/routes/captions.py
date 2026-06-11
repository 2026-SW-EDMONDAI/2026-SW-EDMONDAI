import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import OrgContext, require_analyst
from schemas.video import CaptionCueOut
from services.video_service import VideoService

router = APIRouter(prefix="/api/v1/orgs/{orgId}", tags=["captions"])


@router.get("/videos/{videoId}/captions/cues", dependencies=[Depends(require_analyst)])
def get_caption_cues(
    orgId: OrgContext,
    videoId: uuid.UUID,
    db: Session = Depends(get_db),
    startMs: int | None = Query(None),
    endMs: int | None = Query(None),
    languageCode: str | None = Query(None),
):
    svc = VideoService(db)
    cues = svc.get_caption_cues(orgId, videoId, start_ms=startMs, end_ms=endMs, language_code=languageCode)
    return {
        "data": [
            CaptionCueOut(seqNo=c.seq_no, startMs=c.start_ms, endMs=c.end_ms, text=c.text).model_dump()
            for c in cues
        ],
        "meta": {
            "requestId": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
