import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GuardrailPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "guardrail_policies"
    __table_args__ = (
        Index("ix_guardrail_org_active", "organization_id", "is_active"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    completion_drop_limit_pp: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=5.0
    )
    transition_drop_limit_pp: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=5.0
    )
    explicit_signal_drop_limit_pp: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=5.0
    )
    min_confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.7
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
