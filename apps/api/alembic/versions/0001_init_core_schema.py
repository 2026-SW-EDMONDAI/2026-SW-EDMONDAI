"""init core schema

Revision ID: 0001
Revises:
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum
    video_status = sa.Enum(
        "draft", "uploaded", "processing", "analyzed", "failed", "archived",
        name="video_status",
    )
    video_status.create(op.get_bind(), checkfirst=True)

    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(40), nullable=False, server_default="operator"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # organization_members
    op.create_table(
        "organization_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("org_role", sa.String(40), nullable=False, server_default="analyst"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # videos
    op.create_table(
        "videos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", video_status, nullable=False, server_default="draft"),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="upload"),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_videos_org_status", "videos", ["organization_id", "status"])
    op.create_index("ix_videos_org_created", "videos", ["organization_id", "created_at"])

    # guardrail_policies
    op.create_table(
        "guardrail_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("completion_drop_limit_pp", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("transition_drop_limit_pp", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("explicit_signal_drop_limit_pp", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("min_confidence_score", sa.Numeric(5, 2), nullable=False, server_default="0.70"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_guardrail_org_active", "guardrail_policies", ["organization_id", "is_active"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id", "created_at"])
    op.create_index("ix_audit_org_created", "audit_logs", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("guardrail_policies")
    op.drop_table("videos")
    op.drop_table("organization_members")
    op.drop_table("users")
    op.drop_table("organizations")
    sa.Enum(name="video_status").drop(op.get_bind(), checkfirst=True)
