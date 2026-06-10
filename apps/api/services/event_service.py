import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import AppException
from models.analytics import LearnerSession, LearningEvent
from models.core import Video
from schemas.event import EventBatchRequest


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_batch(
        self,
        body: EventBatchRequest,
        player_context: dict,
    ) -> tuple[uuid.UUID, int, int, int]:
        """Returns (learner_session_id, accepted, rejected, duplicates)."""
        token_org_id = uuid.UUID(player_context["orgId"])
        token_video_id = uuid.UUID(player_context["videoId"])

        if body.organizationId != token_org_id or body.videoId != token_video_id:
            raise AppException(
                code="PLAYER_TOKEN_INVALID",
                message="Token does not match request org/video.",
                status_code=403,
            )

        video = self.db.scalar(
            select(Video).where(
                Video.id == body.videoId,
                Video.organization_id == body.organizationId,
            )
        )
        if not video:
            raise AppException(
                code="VIDEO_NOT_FOUND", message="Video not found.", status_code=404
            )

        session = self._resolve_session(body, player_context)

        accepted = 0
        duplicates = 0
        rejected = 0

        existing_client_ids: set[str] = set(
            self.db.scalars(
                select(LearningEvent.client_event_id).where(
                    LearningEvent.learner_session_id == session.id,
                    LearningEvent.client_event_id.in_(
                        [e.clientEventId for e in body.events]
                    ),
                )
            ).all()
        )

        for evt in body.events:
            if evt.clientEventId in existing_client_ids:
                duplicates += 1
                continue

            self.db.add(
                LearningEvent(
                    organization_id=body.organizationId,
                    video_id=body.videoId,
                    segment_set_id=body.segmentSetId,
                    segment_id=evt.segmentId,
                    learner_session_id=session.id,
                    client_event_id=evt.clientEventId,
                    signal_mode=evt.signalMode,
                    event_type=evt.eventType,
                    event_value=evt.eventValue,
                    position_ms=evt.positionMs,
                    payload=evt.payload,
                    occurred_at=evt.occurredAt,
                )
            )
            existing_client_ids.add(evt.clientEventId)
            accepted += 1

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise AppException(
                code="EVENT_BATCH_INVALID",
                message="Failed to persist events due to integrity violation.",
                status_code=409,
            )

        return session.id, accepted, rejected, duplicates

    def _resolve_session(
        self,
        body: EventBatchRequest,
        player_context: dict,
    ) -> LearnerSession:
        if body.learnerSessionId:
            session = self.db.scalar(
                select(LearnerSession).where(
                    LearnerSession.id == body.learnerSessionId,
                    LearnerSession.video_id == body.videoId,
                )
            )
            if session:
                return session

        anon_key = (
            body.anonymousUserKey
            or player_context.get("anonymousUserKey")
            or f"anon_{uuid.uuid4().hex[:16]}"
        )

        session = LearnerSession(
            id=body.learnerSessionId or uuid.uuid4(),
            video_id=body.videoId,
            anonymous_user_key=anon_key,
            session_started_at=datetime.now(timezone.utc),
            device_type=body.deviceType,
            platform=body.devicePlatform,
            country_code=body.countryCode,
        )
        self.db.add(session)
        self.db.flush()
        return session
