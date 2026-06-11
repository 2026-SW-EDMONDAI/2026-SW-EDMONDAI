"""m3 event collection and funnel analytics

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID, ENUM as PG_ENUM

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SIGNAL_MODE_VALUES = ("implicit", "explicit", "ad")
EVENT_TYPE_VALUES = (
    "video_start",
    "segment_start",
    "segment_complete",
    "pause",
    "seek_back",
    "rewatch",
    "speed_change",
    "subtitle_toggle",
    "next_segment_start",
    "exit",
    "confidence_check_submit",
    "quiz_submit",
    "concept_select",
    "summary_submit",
    "ad_impression",
    "ad_click",
)


def upgrade() -> None:
    signal_values = ",".join(f"'{v}'" for v in SIGNAL_MODE_VALUES)
    op.execute(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='signal_mode') THEN "
        f"CREATE TYPE signal_mode AS ENUM ({signal_values}); "
        f"END IF; END $$;"
    )
    event_values = ",".join(f"'{v}'" for v in EVENT_TYPE_VALUES)
    op.execute(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='event_type') THEN "
        f"CREATE TYPE event_type AS ENUM ({event_values}); "
        f"END IF; END $$;"
    )

    # learner_sessions
    op.create_table(
        "learner_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("anonymous_user_key", sa.String(128), nullable=False),
        sa.Column(
            "session_started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("session_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_type", sa.String(30), nullable=True),
        sa.Column("platform", sa.String(30), nullable=True),
        sa.Column("country_code", sa.String(5), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_learner_sessions_video_started",
        "learner_sessions",
        ["video_id", "session_started_at"],
    )
    op.create_index(
        "ix_learner_sessions_anon_key", "learner_sessions", ["anonymous_user_key"]
    )

    # learning_events
    op.create_table(
        "learning_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column(
            "segment_set_id",
            UUID(as_uuid=True),
            sa.ForeignKey("segment_sets.id"),
            nullable=True,
        ),
        sa.Column(
            "segment_id", UUID(as_uuid=True), sa.ForeignKey("segments.id"), nullable=True
        ),
        sa.Column(
            "learner_session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("learner_sessions.id"),
            nullable=False,
        ),
        sa.Column("client_event_id", sa.String(80), nullable=False),
        sa.Column(
            "signal_mode",
            PG_ENUM(*SIGNAL_MODE_VALUES, name="signal_mode", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            PG_ENUM(*EVENT_TYPE_VALUES, name="event_type", create_type=False),
            nullable=False,
        ),
        sa.Column("event_value", sa.String(100), nullable=True),
        sa.Column("position_ms", sa.Integer, nullable=True),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "learner_session_id", "client_event_id", name="uq_learning_event_client_id"
        ),
    )
    op.create_index(
        "ix_learning_events_video_occurred",
        "learning_events",
        ["video_id", "occurred_at"],
    )
    op.create_index(
        "ix_learning_events_segment_type_occurred",
        "learning_events",
        ["segment_id", "event_type", "occurred_at"],
    )
    op.create_index(
        "ix_learning_events_session_occurred",
        "learning_events",
        ["learner_session_id", "occurred_at"],
    )
    op.create_index(
        "ix_learning_events_signal_type",
        "learning_events",
        ["signal_mode", "event_type"],
    )

    # segment_metric_snapshots
    op.create_table(
        "segment_metric_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column(
            "segment_set_id",
            UUID(as_uuid=True),
            sa.ForeignKey("segment_sets.id"),
            nullable=False,
        ),
        sa.Column(
            "segment_id", UUID(as_uuid=True), sa.ForeignKey("segments.id"), nullable=False
        ),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("cohort_type", sa.String(30), nullable=False, server_default="all"),
        sa.Column("placement_id", UUID(as_uuid=True), nullable=True),
        sa.Column("viewers_started", sa.Integer, nullable=False, server_default="0"),
        sa.Column("viewers_completed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("dropout_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("rewatch_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "next_transition_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("avg_pause_count", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column(
            "avg_seek_back_count", sa.Numeric(8, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "avg_speed_change_count",
            sa.Numeric(8, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "explicit_response_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("confidence_positive_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("confidence_unsure_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("confidence_review_again_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("learning_stability_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("risk_flags", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "segment_id",
            "metric_date",
            "cohort_type",
            "placement_id",
            name="uq_segment_metric_snapshot",
        ),
    )
    op.create_index(
        "ix_segment_metric_video_date",
        "segment_metric_snapshots",
        ["video_id", "metric_date"],
    )
    op.create_index(
        "ix_segment_metric_segment_date",
        "segment_metric_snapshots",
        ["segment_id", "metric_date"],
    )

    # video_metric_snapshots
    op.create_table(
        "video_metric_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("cohort_type", sa.String(30), nullable=False, server_default="all"),
        sa.Column("placement_id", UUID(as_uuid=True), nullable=True),
        sa.Column("total_viewers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("avg_watch_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "avg_watch_time_sec", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column("next_transition_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("explicit_response_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "video_id",
            "metric_date",
            "cohort_type",
            "placement_id",
            name="uq_video_metric_snapshot",
        ),
    )
    op.create_index(
        "ix_video_metric_date", "video_metric_snapshots", ["video_id", "metric_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_video_metric_date", table_name="video_metric_snapshots")
    op.drop_table("video_metric_snapshots")

    op.drop_index(
        "ix_segment_metric_segment_date", table_name="segment_metric_snapshots"
    )
    op.drop_index("ix_segment_metric_video_date", table_name="segment_metric_snapshots")
    op.drop_table("segment_metric_snapshots")

    op.drop_index("ix_learning_events_signal_type", table_name="learning_events")
    op.drop_index("ix_learning_events_session_occurred", table_name="learning_events")
    op.drop_index(
        "ix_learning_events_segment_type_occurred", table_name="learning_events"
    )
    op.drop_index("ix_learning_events_video_occurred", table_name="learning_events")
    op.drop_table("learning_events")

    op.drop_index("ix_learner_sessions_anon_key", table_name="learner_sessions")
    op.drop_index("ix_learner_sessions_video_started", table_name="learner_sessions")
    op.drop_table("learner_sessions")

    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS signal_mode")
