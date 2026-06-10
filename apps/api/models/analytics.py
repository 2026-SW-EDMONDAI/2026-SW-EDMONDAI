import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDPrimaryKeyMixin


class SignalMode(str, enum.Enum):
    implicit = "implicit"
    explicit = "explicit"
    ad = "ad"


class EventType(str, enum.Enum):
    video_start = "video_start"
    segment_start = "segment_start"
    segment_complete = "segment_complete"
    pause = "pause"
    seek_back = "seek_back"
    rewatch = "rewatch"
    speed_change = "speed_change"
    subtitle_toggle = "subtitle_toggle"
    next_segment_start = "next_segment_start"
    exit = "exit"
    confidence_check_submit = "confidence_check_submit"
    quiz_submit = "quiz_submit"
    concept_select = "concept_select"
    summary_submit = "summary_submit"
    ad_impression = "ad_impression"
    ad_click = "ad_click"


class LearnerSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learner_sessions"
    __table_args__ = (
        Index("ix_learner_sessions_video_started", "video_id", "session_started_at"),
        Index("ix_learner_sessions_anon_key", "anonymous_user_key"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    anonymous_user_key: Mapped[str] = mapped_column(String(128), nullable=False)
    session_started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    session_ended_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    device_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        UniqueConstraint(
            "learner_session_id", "client_event_id", name="uq_learning_event_client_id"
        ),
        Index("ix_learning_events_video_occurred", "video_id", "occurred_at"),
        Index(
            "ix_learning_events_segment_type_occurred",
            "segment_id",
            "event_type",
            "occurred_at",
        ),
        Index("ix_learning_events_session_occurred", "learner_session_id", "occurred_at"),
        Index("ix_learning_events_signal_type", "signal_mode", "event_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    segment_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segment_sets.id"), nullable=True
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=True
    )
    learner_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_sessions.id"), nullable=False
    )
    client_event_id: Mapped[str] = mapped_column(String(80), nullable=False)
    signal_mode: Mapped[SignalMode] = mapped_column(
        Enum(SignalMode, name="signal_mode", create_constraint=True),
        nullable=False,
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type", create_constraint=True),
        nullable=False,
    )
    event_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class SegmentMetricSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "segment_metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "segment_id",
            "metric_date",
            "cohort_type",
            "placement_id",
            name="uq_segment_metric_snapshot",
        ),
        Index("ix_segment_metric_video_date", "video_id", "metric_date"),
        Index("ix_segment_metric_segment_date", "segment_id", "metric_date"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    segment_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segment_sets.id"), nullable=False
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False
    )
    metric_date: Mapped[sa.Date] = mapped_column(Date, nullable=False)
    cohort_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="all"
    )
    placement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    viewers_started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    viewers_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    dropout_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    rewatch_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    next_transition_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0
    )
    avg_pause_count: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    avg_seek_back_count: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=0
    )
    avg_speed_change_count: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=0
    )
    explicit_response_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0
    )
    confidence_positive_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    confidence_unsure_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    confidence_review_again_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    learning_stability_score: Mapped[float | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    risk_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class VideoMetricSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "video_metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "video_id",
            "metric_date",
            "cohort_type",
            "placement_id",
            name="uq_video_metric_snapshot",
        ),
        Index("ix_video_metric_date", "video_id", "metric_date"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    metric_date: Mapped[sa.Date] = mapped_column(Date, nullable=False)
    cohort_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="all"
    )
    placement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    total_viewers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    avg_watch_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    avg_watch_time_sec: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    next_transition_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    explicit_response_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
