import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.player_auth import PlayerContext
from schemas.event import EventBatchRequest, EventBatchResponse
from services.event_service import EventService

router = APIRouter(prefix="/player", tags=["player-events"])


def _meta() -> dict:
    return {
        "requestId": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/events/batch", status_code=202)
def ingest_events(
    body: EventBatchRequest,
    player_context: PlayerContext,
    db: Session = Depends(get_db),
):
    svc = EventService(db)
    session_id, accepted, rejected, duplicates = svc.ingest_batch(body, player_context)
    response = EventBatchResponse(
        accepted=accepted,
        rejected=rejected,
        learnerSessionId=session_id,
        duplicates=duplicates,
    )
    return {"data": response.model_dump(mode="json"), "meta": _meta()}
