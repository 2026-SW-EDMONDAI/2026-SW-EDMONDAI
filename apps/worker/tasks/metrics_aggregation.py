"""
Metrics aggregation Celery task.

Flow:
  1. For (video_id, metric_date), scan learning_events within UTC day
  2. Group by segment_id, compute implicit/explicit metrics
  3. Compute risk flags from absolute thresholds
  4. Upsert segment_metric_snapshots and video_metric_snapshots

Idempotent: re-running for the same (segment_id, metric_date, cohort_type='all',
placement_id=NULL) replaces the existing row via UNIQUE constraint.
"""
import logging
import os
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


# ── Risk-flag thresholds (MVP, absolute values) ────────────────────────────

DROPOUT_SPIKE_THRESHOLD = 0.30
REWATCH_SPIKE_THRESHOLD = 0.25
LOW_EXPLICIT_SIGNAL_THRESHOLD = 0.15
TRANSITION_DROP_THRESHOLD = 0.60
MIN_VIEWERS_FOR_FLAGS = 30  # statistical floor

STABILITY_WEIGHTS = {
    "completion": 0.4,
    "transition": 0.3,
    "confidence": 0.3,
}


def _get_db_session():
    db_url = (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', 'segmentflow')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'segmentflow_dev')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'segmentflow')}"
    )
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


# ── Risk flag computation ──────────────────────────────────────────────────

def compute_risk_flags(metrics: dict, viewers_started: int) -> list[str]:
    """Return a list of risk flag identifiers for a segment."""
    flags: list[str] = []
    if viewers_started < MIN_VIEWERS_FOR_FLAGS:
        return flags
    if metrics["dropout_rate"] >= DROPOUT_SPIKE_THRESHOLD:
        flags.append("dropout_spike")
    if metrics["rewatch_rate"] >= REWATCH_SPIKE_THRESHOLD:
        flags.append("rewatch_spike")
    if metrics["explicit_response_rate"] < LOW_EXPLICIT_SIGNAL_THRESHOLD:
        flags.append("low_explicit_signal")
    if metrics["next_transition_rate"] < TRANSITION_DROP_THRESHOLD:
        flags.append("transition_drop")
    return flags


def compute_stability_score(metrics: dict) -> float:
    """Weighted 0..1 stability score; null-safe."""
    completion = float(metrics["completion_rate"])
    transition = float(metrics["next_transition_rate"])
    raw_confidence = metrics.get("confidence_positive_rate")
    confidence = 0.5 if raw_confidence is None else float(raw_confidence)
    score = (
        STABILITY_WEIGHTS["completion"] * completion
        + STABILITY_WEIGHTS["transition"] * transition
        + STABILITY_WEIGHTS["confidence"] * confidence
    )
    return round(score, 3)


# ── Aggregation core ───────────────────────────────────────────────────────

def _safe_div(num: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return round(num / denom, 4)


def _aggregate_segment_metrics(events: list) -> dict:
    """Compute per-segment metric dict from raw events. `events` is for one segment."""
    sessions_started: set = set()
    sessions_completed: set = set()
    pause_count = 0
    seek_back_count = 0
    speed_change_count = 0
    rewatch_count = 0
    next_transition_count = 0
    explicit_count = 0
    confidence_positive = 0
    confidence_unsure = 0
    confidence_review = 0

    for e in events:
        sid = e.learner_session_id
        if e.event_type.value == "segment_start":
            sessions_started.add(sid)
        elif e.event_type.value == "segment_complete":
            sessions_completed.add(sid)
        elif e.event_type.value == "pause":
            pause_count += 1
        elif e.event_type.value == "seek_back":
            seek_back_count += 1
        elif e.event_type.value == "speed_change":
            speed_change_count += 1
        elif e.event_type.value == "rewatch":
            rewatch_count += 1
        elif e.event_type.value == "next_segment_start":
            next_transition_count += 1
        elif e.event_type.value == "confidence_check_submit":
            explicit_count += 1
            if e.event_value == "understood":
                confidence_positive += 1
            elif e.event_value == "unsure":
                confidence_unsure += 1
            elif e.event_value == "review_again":
                confidence_review += 1

    viewers_started = len(sessions_started)
    viewers_completed = len(sessions_completed)
    completion_rate = _safe_div(viewers_completed, viewers_started)

    metrics = {
        "viewers_started": viewers_started,
        "viewers_completed": viewers_completed,
        "completion_rate": completion_rate,
        "dropout_rate": round(1.0 - completion_rate, 4) if viewers_started else 0.0,
        "rewatch_rate": _safe_div(rewatch_count, viewers_started),
        "next_transition_rate": _safe_div(next_transition_count, viewers_completed),
        "avg_pause_count": _safe_div(pause_count, viewers_started),
        "avg_seek_back_count": _safe_div(seek_back_count, viewers_started),
        "avg_speed_change_count": _safe_div(speed_change_count, viewers_started),
        "explicit_response_rate": _safe_div(explicit_count, viewers_started),
        "confidence_positive_rate": (
            _safe_div(confidence_positive, explicit_count) if explicit_count else None
        ),
        "confidence_unsure_rate": (
            _safe_div(confidence_unsure, explicit_count) if explicit_count else None
        ),
        "confidence_review_again_rate": (
            _safe_div(confidence_review, explicit_count) if explicit_count else None
        ),
    }
    metrics["learning_stability_score"] = compute_stability_score(metrics)
    return metrics


# ── Main runner (testable without Celery) ──────────────────────────────────

def _run_aggregate(video_id: str, metric_date: date | str, db=None) -> dict:
    """
    Aggregate raw learning_events for one (video, day) into segment/video snapshots.

    cohort_type='all', placement_id=NULL for the MVP path.
    """
    if isinstance(metric_date, str):
        metric_date = date.fromisoformat(metric_date)

    owns_db = db is None
    if owns_db:
        db = _get_db_session()
    try:
        from models.analytics import (
            LearningEvent,
            SegmentMetricSnapshot,
            VideoMetricSnapshot,
        )
        from models.segment import Segment, SegmentSet, SegmentSetStatus

        vid_uuid = uuid.UUID(video_id)
        day_start = datetime.combine(
            metric_date, datetime.min.time(), tzinfo=timezone.utc
        )
        day_end = day_start + timedelta(days=1)

        latest_set = db.scalar(
            select(SegmentSet)
            .where(SegmentSet.video_id == vid_uuid)
            .order_by(SegmentSet.version_no.desc())
        )
        if not latest_set:
            logger.warning("Video %s has no segment_set; skipping", video_id)
            return {"status": "skipped", "reason": "no_segment_set"}
        segment_set_id = latest_set.id

        segments = db.scalars(
            select(Segment).where(Segment.segment_set_id == segment_set_id)
        ).all()
        segment_ids = [s.id for s in segments]
        if not segment_ids:
            return {"status": "skipped", "reason": "no_segments"}

        events = db.scalars(
            select(LearningEvent).where(
                LearningEvent.video_id == vid_uuid,
                LearningEvent.occurred_at >= day_start,
                LearningEvent.occurred_at < day_end,
                LearningEvent.segment_id.in_(segment_ids),
            )
        ).all()

        events_by_segment: dict[uuid.UUID, list] = defaultdict(list)
        for e in events:
            if e.segment_id:
                events_by_segment[e.segment_id].append(e)

        snapshot_count = 0
        all_sessions: set = set()
        video_completed_sessions: set = set()

        for seg in segments:
            seg_events = events_by_segment.get(seg.id, [])
            metrics = _aggregate_segment_metrics(seg_events)
            risk_flags = compute_risk_flags(metrics, metrics["viewers_started"])

            stmt = pg_insert(SegmentMetricSnapshot.__table__).values(
                id=uuid.uuid4(),
                video_id=vid_uuid,
                segment_set_id=segment_set_id,
                segment_id=seg.id,
                metric_date=metric_date,
                cohort_type="all",
                placement_id=None,
                risk_flags=risk_flags,
                **{
                    k: Decimal(str(v)) if isinstance(v, float) else v
                    for k, v in metrics.items()
                    if v is not None
                },
            )
            update_cols = {
                col.name: col
                for col in stmt.excluded
                if col.name not in ("id", "created_at")
            }
            stmt = stmt.on_conflict_do_update(
                constraint="uq_segment_metric_snapshot",
                set_=update_cols,
            )
            db.execute(stmt)
            snapshot_count += 1

            for e in seg_events:
                all_sessions.add(e.learner_session_id)
                if e.event_type.value == "segment_complete":
                    video_completed_sessions.add(e.learner_session_id)

        # Video-level snapshot
        total_viewers = len(all_sessions)
        completion_rate = _safe_div(len(video_completed_sessions), total_viewers)
        video_stmt = pg_insert(VideoMetricSnapshot.__table__).values(
            id=uuid.uuid4(),
            video_id=vid_uuid,
            metric_date=metric_date,
            cohort_type="all",
            placement_id=None,
            total_viewers=total_viewers,
            completion_rate=Decimal(str(completion_rate)),
            avg_watch_rate=Decimal("0"),
            avg_watch_time_sec=Decimal("0"),
            next_transition_rate=None,
            explicit_response_rate=None,
        )
        video_update_cols = {
            col.name: col
            for col in video_stmt.excluded
            if col.name not in ("id", "created_at")
        }
        video_stmt = video_stmt.on_conflict_do_update(
            constraint="uq_video_metric_snapshot",
            set_=video_update_cols,
        )
        db.execute(video_stmt)

        db.commit()
        logger.info(
            "Aggregated video=%s date=%s segments=%d viewers=%d",
            video_id, metric_date, snapshot_count, total_viewers,
        )
        return {
            "status": "success",
            "segment_snapshots": snapshot_count,
            "total_viewers": total_viewers,
        }

    except Exception:
        db.rollback()
        raise
    finally:
        if owns_db:
            db.close()


# ── Celery task ────────────────────────────────────────────────────────────

@shared_task(
    name="worker.tasks.metrics_aggregation.aggregate_video_metrics",
    queue="metrics-aggregation",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def aggregate_video_metrics(self, video_id: str, metric_date: str) -> dict:
    """Celery task wrapper around _run_aggregate."""
    try:
        return _run_aggregate(video_id, metric_date)
    except Exception as exc:
        logger.exception(
            "Error aggregating video=%s date=%s: %s", video_id, metric_date, exc
        )
        raise self.retry(exc=exc)
