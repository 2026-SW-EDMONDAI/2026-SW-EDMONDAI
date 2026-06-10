import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import AppException
from models.analytics import SegmentMetricSnapshot, VideoMetricSnapshot
from models.core import Video
from models.segment import Segment, SegmentSet


class FunnelService:
    def __init__(self, db: Session):
        self.db = db

    def get_video_funnel(
        self,
        org_id: uuid.UUID,
        video_id: uuid.UUID,
        segment_set_id: uuid.UUID,
        metric_date: date | None = None,
        cohort_type: str = "all",
        placement_id: uuid.UUID | None = None,
    ) -> dict:
        video = self.db.scalar(
            select(Video).where(
                Video.id == video_id, Video.organization_id == org_id
            )
        )
        if not video:
            raise AppException(
                code="VIDEO_NOT_FOUND", message="Video not found.", status_code=404
            )

        segment_set = self.db.scalar(
            select(SegmentSet).where(
                SegmentSet.id == segment_set_id, SegmentSet.video_id == video_id
            )
        )
        if not segment_set:
            raise AppException(
                code="SEGMENT_SET_NOT_FOUND",
                message="Segment set not found.",
                status_code=404,
            )

        resolved_date = metric_date or self._latest_metric_date(
            video_id, cohort_type, placement_id
        )

        segments = self.db.scalars(
            select(Segment)
            .where(Segment.segment_set_id == segment_set_id)
            .order_by(Segment.seq_no)
        ).all()

        snapshots = self.db.scalars(
            select(SegmentMetricSnapshot).where(
                SegmentMetricSnapshot.video_id == video_id,
                SegmentMetricSnapshot.segment_set_id == segment_set_id,
                SegmentMetricSnapshot.metric_date == resolved_date,
                SegmentMetricSnapshot.cohort_type == cohort_type,
                SegmentMetricSnapshot.placement_id.is_(placement_id)
                if placement_id is None
                else SegmentMetricSnapshot.placement_id == placement_id,
            )
        ).all() if resolved_date else []

        snap_by_segment = {s.segment_id: s for s in snapshots}

        segments_payload = []
        for seg in segments:
            snap = snap_by_segment.get(seg.id)
            segments_payload.append(
                {
                    "segment": {
                        "id": str(seg.id),
                        "seqNo": seg.seq_no,
                        "title": seg.title,
                        "startMs": seg.start_ms,
                        "endMs": seg.end_ms,
                    },
                    "metrics": _snapshot_to_metrics(snap),
                    "riskFlags": list(snap.risk_flags) if snap and snap.risk_flags else [],
                }
            )

        video_snap = None
        if resolved_date:
            video_snap = self.db.scalar(
                select(VideoMetricSnapshot).where(
                    VideoMetricSnapshot.video_id == video_id,
                    VideoMetricSnapshot.metric_date == resolved_date,
                    VideoMetricSnapshot.cohort_type == cohort_type,
                    VideoMetricSnapshot.placement_id.is_(placement_id)
                    if placement_id is None
                    else VideoMetricSnapshot.placement_id == placement_id,
                )
            )

        return {
            "videoSummary": {
                "videoId": str(video_id),
                "segmentSetId": str(segment_set_id),
                "metricDate": resolved_date.isoformat() if resolved_date else None,
                "completionRate": (
                    float(video_snap.completion_rate) if video_snap else 0.0
                ),
                "nextTransitionRate": (
                    float(video_snap.next_transition_rate)
                    if video_snap and video_snap.next_transition_rate is not None
                    else None
                ),
                "explicitResponseRate": (
                    float(video_snap.explicit_response_rate)
                    if video_snap and video_snap.explicit_response_rate is not None
                    else None
                ),
            },
            "segments": segments_payload,
        }

    def get_segment_timeseries(
        self,
        org_id: uuid.UUID,
        segment_id: uuid.UUID,
        date_from: date,
        date_to: date,
        cohort_type: str = "all",
        placement_id: uuid.UUID | None = None,
    ) -> dict:
        segment = self.db.scalar(select(Segment).where(Segment.id == segment_id))
        if not segment:
            raise AppException(
                code="NOT_FOUND", message="Segment not found.", status_code=404
            )

        segment_set = self.db.scalar(
            select(SegmentSet).where(SegmentSet.id == segment.segment_set_id)
        )
        video = self.db.scalar(select(Video).where(Video.id == segment_set.video_id))
        if not video or video.organization_id != org_id:
            raise AppException(code="FORBIDDEN", message="Forbidden.", status_code=403)

        rows = self.db.scalars(
            select(SegmentMetricSnapshot)
            .where(
                SegmentMetricSnapshot.segment_id == segment_id,
                SegmentMetricSnapshot.metric_date >= date_from,
                SegmentMetricSnapshot.metric_date <= date_to,
                SegmentMetricSnapshot.cohort_type == cohort_type,
                SegmentMetricSnapshot.placement_id.is_(placement_id)
                if placement_id is None
                else SegmentMetricSnapshot.placement_id == placement_id,
            )
            .order_by(SegmentMetricSnapshot.metric_date)
        ).all()

        return {
            "segmentId": str(segment_id),
            "series": [
                {
                    "metricDate": r.metric_date.isoformat(),
                    "completionRate": float(r.completion_rate),
                    "nextTransitionRate": float(r.next_transition_rate),
                    "explicitResponseRate": float(r.explicit_response_rate),
                }
                for r in rows
            ],
        }

    def _latest_metric_date(
        self,
        video_id: uuid.UUID,
        cohort_type: str,
        placement_id: uuid.UUID | None,
    ) -> date | None:
        from sqlalchemy import func

        return self.db.scalar(
            select(func.max(SegmentMetricSnapshot.metric_date)).where(
                SegmentMetricSnapshot.video_id == video_id,
                SegmentMetricSnapshot.cohort_type == cohort_type,
                SegmentMetricSnapshot.placement_id.is_(placement_id)
                if placement_id is None
                else SegmentMetricSnapshot.placement_id == placement_id,
            )
        )


def _snapshot_to_metrics(snap) -> dict:
    if not snap:
        return {
            "viewersStarted": 0,
            "viewersCompleted": 0,
            "completionRate": 0.0,
            "dropoutRate": 0.0,
            "rewatchRate": 0.0,
            "nextTransitionRate": 0.0,
            "avgPauseCount": 0.0,
            "avgSeekBackCount": 0.0,
            "avgSpeedChangeCount": 0.0,
            "explicitResponseRate": 0.0,
            "confidencePositiveRate": None,
            "confidenceUnsureRate": None,
            "confidenceReviewAgainRate": None,
            "learningStabilityScore": None,
        }
    return {
        "viewersStarted": snap.viewers_started,
        "viewersCompleted": snap.viewers_completed,
        "completionRate": float(snap.completion_rate),
        "dropoutRate": float(snap.dropout_rate),
        "rewatchRate": float(snap.rewatch_rate),
        "nextTransitionRate": float(snap.next_transition_rate),
        "avgPauseCount": float(snap.avg_pause_count),
        "avgSeekBackCount": float(snap.avg_seek_back_count),
        "avgSpeedChangeCount": float(snap.avg_speed_change_count),
        "explicitResponseRate": float(snap.explicit_response_rate),
        "confidencePositiveRate": (
            float(snap.confidence_positive_rate)
            if snap.confidence_positive_rate is not None
            else None
        ),
        "confidenceUnsureRate": (
            float(snap.confidence_unsure_rate)
            if snap.confidence_unsure_rate is not None
            else None
        ),
        "confidenceReviewAgainRate": (
            float(snap.confidence_review_again_rate)
            if snap.confidence_review_again_rate is not None
            else None
        ),
        "learningStabilityScore": (
            float(snap.learning_stability_score)
            if snap.learning_stability_score is not None
            else None
        ),
    }
