import enum
import uuid

import sqlalchemy as sa
from sqlalchemy import (
    CheckConstraint,
    Enum,
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


class SegmentSetStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"
    archived = "archived"


class SegmentSet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "segment_sets"
    __table_args__ = (
        UniqueConstraint("video_id", "version_no", name="uq_segment_set_version"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SegmentSetStatus] = mapped_column(
        Enum(SegmentSetStatus, name="segment_set_status", create_constraint=True),
        nullable=False,
        default=SegmentSetStatus.draft,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="auto")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    video = relationship("Video", back_populates="segment_sets")
    segments = relationship(
        "Segment",
        back_populates="segment_set",
        order_by="Segment.seq_no",
        cascade="all, delete-orphan",
    )


class Segment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "segments"
    __table_args__ = (
        UniqueConstraint("segment_set_id", "seq_no", name="uq_segment_seq"),
        CheckConstraint("start_ms < end_ms", name="ck_segment_time_range"),
        Index("ix_segments_set_start", "segment_set_id", "start_ms"),
    )

    segment_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segment_sets.id"), nullable=False
    )
    seq_no: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key_concepts: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="auto")

    segment_set = relationship("SegmentSet", back_populates="segments")
