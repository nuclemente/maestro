"""create oneonone tables

Revision ID: a3b7c9d2e4f1
Revises: f8129533384f
Create Date: 2026-05-22 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b7c9d2e4f1"
down_revision: Union[str, None] = "f8129533384f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oneonone_tracks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oneonone_tracks_person_id"),
        "oneonone_tracks",
        ["person_id"],
        unique=True,
    )

    op.create_table(
        "oneonone_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("track_id", sa.String(length=36), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("planned", "done", "cancelled", name="session_status"),
            nullable=False,
        ),
        sa.Column("external_event_id", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["track_id"], ["oneonone_tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_event_id"),
    )
    op.create_index("ix_sessions_track_status", "oneonone_sessions", ["track_id", "status"])
    op.create_index(
        op.f("ix_oneonone_sessions_track_id"),
        "oneonone_sessions",
        ["track_id"],
        unique=False,
    )

    op.create_table(
        "oneonone_topics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("manual", "slack_collection", "from_transcript", name="topic_source"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "discussed", "parked", name="topic_status"),
            nullable=False,
        ),
        sa.Column("enrichment", sa.JSON(), nullable=True),
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["oneonone_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oneonone_topics_session_id"),
        "oneonone_topics",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "oneonone_transcripts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analysis_stale", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["oneonone_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "oneonone_action_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transcript_id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "owner",
            sa.Enum("em", "person", "other", name="action_item_owner"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "done", name="action_item_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["transcript_id"], ["oneonone_transcripts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oneonone_action_items_transcript_id"),
        "oneonone_action_items",
        ["transcript_id"],
        unique=False,
    )

    op.create_table(
        "oneonone_collection_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.Column("slack_channel_id", sa.String(length=64), nullable=False),
        sa.Column("sent_message_ts", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("awaiting", "closed", name="collection_status"),
            nullable=False,
        ),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["oneonone_sessions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oneonone_collection_requests_session_id"),
        "oneonone_collection_requests",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oneonone_collection_requests_person_id"),
        "oneonone_collection_requests",
        ["person_id"],
        unique=False,
    )
    # Garante 1 awaiting por session.
    op.create_index(
        "uq_collection_awaiting_per_session",
        "oneonone_collection_requests",
        ["session_id"],
        unique=True,
        sqlite_where=sa.text("status = 'awaiting'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_collection_awaiting_per_session", table_name="oneonone_collection_requests"
    )
    op.drop_index(
        op.f("ix_oneonone_collection_requests_person_id"),
        table_name="oneonone_collection_requests",
    )
    op.drop_index(
        op.f("ix_oneonone_collection_requests_session_id"),
        table_name="oneonone_collection_requests",
    )
    op.drop_table("oneonone_collection_requests")

    op.drop_index(
        op.f("ix_oneonone_action_items_transcript_id"),
        table_name="oneonone_action_items",
    )
    op.drop_table("oneonone_action_items")

    op.drop_table("oneonone_transcripts")

    op.drop_index(op.f("ix_oneonone_topics_session_id"), table_name="oneonone_topics")
    op.drop_table("oneonone_topics")

    op.drop_index(op.f("ix_oneonone_sessions_track_id"), table_name="oneonone_sessions")
    op.drop_index("ix_sessions_track_status", table_name="oneonone_sessions")
    op.drop_table("oneonone_sessions")

    op.drop_index(op.f("ix_oneonone_tracks_person_id"), table_name="oneonone_tracks")
    op.drop_table("oneonone_tracks")
