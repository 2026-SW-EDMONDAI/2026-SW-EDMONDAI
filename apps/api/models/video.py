import uuid

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VideoAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "video_assets"
    __table_args__ = (
        Index("ix_video_assets_video_type", "video_id", "asset_type"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    video = relationship("Video", back_populates="assets")


class CaptionTrack(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "caption_tracks"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="ko")
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="uploaded")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    video = relationship("Video", back_populates="caption_tracks")
    cues = relationship("CaptionCue", back_populates="track", cascade="all, delete-orphan")


class CaptionCue(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "caption_cues"
    __table_args__ = (
        UniqueConstraint("caption_track_id", "seq_no", name="uq_caption_cue_seq"),
        Index("ix_caption_cues_track_start", "caption_track_id", "start_ms"),
    )

    caption_track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("caption_tracks.id"), nullable=False
    )
    seq_no: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    track = relationship("CaptionTrack", back_populates="cues")


class VideoSignalConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_signal_configs"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), unique=True, nullable=False
    )
    confidence_check_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    quiz_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    concept_select_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    video = relationship("Video", back_populates="signal_config")
