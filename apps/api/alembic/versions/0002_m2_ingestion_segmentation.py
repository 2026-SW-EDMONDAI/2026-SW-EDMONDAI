"""m2 ingestion segmentation

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum: segment_set_status
    segment_set_status = sa.Enum(
        "draft", "finalized", "archived",
        name="segment_set_status",
    )
    segment_set_status.create(op.get_bind(), checkfirst=True)

    # video_assets
    op.create_table(
        "video_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("asset_type", sa.String(30), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_video_assets_video_type", "video_assets", ["video_id", "asset_type"])

    # caption_tracks
    op.create_table(
        "caption_tracks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("language_code", sa.String(10), nullable=False, server_default="ko"),
        sa.Column("source", sa.String(30), nullable=False, server_default="uploaded"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # caption_cues
    op.create_table(
        "caption_cues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("caption_track_id", UUID(as_uuid=True), sa.ForeignKey("caption_tracks.id"), nullable=False),
        sa.Column("seq_no", sa.Integer, nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("caption_track_id", "seq_no", name="uq_caption_cue_seq"),
    )
    op.create_index("ix_caption_cues_track_start", "caption_cues", ["caption_track_id", "start_ms"])

    # video_signal_configs
    op.create_table(
        "video_signal_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), unique=True, nullable=False),
        sa.Column("confidence_check_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("quiz_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("concept_select_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("summary_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("config_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # segment_sets
    op.create_table(
        "segment_sets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("video_id", UUID(as_uuid=True), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("status", segment_set_status, nullable=False, server_default="draft"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="auto"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("video_id", "version_no", name="uq_segment_set_version"),
    )

    # segments
    op.create_table(
        "segments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_set_id", UUID(as_uuid=True), sa.ForeignKey("segment_sets.id"), nullable=False),
        sa.Column("seq_no", sa.Integer, nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("key_concepts", JSONB, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="auto"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("segment_set_id", "seq_no", name="uq_segment_seq"),
        sa.CheckConstraint("start_ms < end_ms", name="ck_segment_time_range"),
    )
    op.create_index("ix_segments_set_start", "segments", ["segment_set_id", "start_ms"])


def downgrade() -> None:
    op.drop_index("ix_segments_set_start", table_name="segments")
    op.drop_table("segments")
    op.drop_table("segment_sets")
    op.drop_table("video_signal_configs")
    op.drop_index("ix_caption_cues_track_start", table_name="caption_cues")
    op.drop_table("caption_cues")
    op.drop_table("caption_tracks")
    op.drop_index("ix_video_assets_video_type", table_name="video_assets")
    op.drop_table("video_assets")
    sa.Enum(name="segment_set_status").drop(op.get_bind(), checkfirst=True)
