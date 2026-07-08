"""initial yijing tables

迁移 ID: 20260708_01
父迁移:
创建时间: 2026-07-08 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = ("nonebot_plugin_yijing",)
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.create_table(
        "nonebot_plugin_yijing_cast_record",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("adapter", sa.String(length=64), nullable=False),
        sa.Column("bot_id", sa.String(length=128), nullable=False),
        sa.Column("group_id", sa.String(length=128), nullable=False),
        sa.Column("user_id_hash", sa.String(length=128), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("question_norm", sa.Text(), nullable=False),
        sa.Column("question_hash", sa.String(length=128), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("coins_json", sa.Text(), nullable=False),
        sa.Column("line_values_json", sa.Text(), nullable=False),
        sa.Column("moving_positions_json", sa.Text(), nullable=False),
        sa.Column("primary_seq", sa.Integer(), nullable=False),
        sa.Column("changed_seq", sa.Integer(), nullable=True),
        sa.Column("preprocess_json", sa.Text(), nullable=False),
        sa.Column("interpretation_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nonebot_plugin_yijing_cast_record")),
        info={"bind_key": "nonebot_plugin_yijing"},
    )
    op.create_index(
        "ix_yijing_cast_group",
        "nonebot_plugin_yijing_cast_record",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_yijing_cast_question",
        "nonebot_plugin_yijing_cast_record",
        ["question_hash"],
        unique=False,
    )
    op.create_index(
        "ix_yijing_cast_time",
        "nonebot_plugin_yijing_cast_record",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_yijing_cast_user",
        "nonebot_plugin_yijing_cast_record",
        ["user_id_hash"],
        unique=False,
    )

    op.create_table(
        "nonebot_plugin_yijing_group_config",
        sa.Column("group_id", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("default_method", sa.String(length=32), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
        sa.Column("daily_limit", sa.Integer(), nullable=False),
        sa.Column("llm_enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("group_id", name=op.f("pk_nonebot_plugin_yijing_group_config")),
        info={"bind_key": "nonebot_plugin_yijing"},
    )

    op.create_table(
        "nonebot_plugin_yijing_group_cooldown",
        sa.Column("group_id", sa.String(length=128), nullable=False),
        sa.Column("last_cast_at", sa.DateTime(), nullable=False),
        sa.Column("last_record_id", sa.String(length=32), nullable=False),
        sa.Column("last_user_hash", sa.String(length=128), nullable=False),
        sa.Column("last_question_norm", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("group_id", name=op.f("pk_nonebot_plugin_yijing_group_cooldown")),
        info={"bind_key": "nonebot_plugin_yijing"},
    )

    op.create_table(
        "nonebot_plugin_yijing_runtime_quota",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.String(length=128), nullable=False),
        sa.Column("user_id_hash", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nonebot_plugin_yijing_runtime_quota")),
        info={"bind_key": "nonebot_plugin_yijing"},
    )
    op.create_index(
        "ix_yijing_quota_group",
        "nonebot_plugin_yijing_runtime_quota",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_yijing_quota_time",
        "nonebot_plugin_yijing_runtime_quota",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_yijing_quota_user",
        "nonebot_plugin_yijing_runtime_quota",
        ["user_id_hash"],
        unique=False,
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_index("ix_yijing_quota_user", table_name="nonebot_plugin_yijing_runtime_quota")
    op.drop_index("ix_yijing_quota_time", table_name="nonebot_plugin_yijing_runtime_quota")
    op.drop_index("ix_yijing_quota_group", table_name="nonebot_plugin_yijing_runtime_quota")
    op.drop_table("nonebot_plugin_yijing_runtime_quota")

    op.drop_table("nonebot_plugin_yijing_group_cooldown")
    op.drop_table("nonebot_plugin_yijing_group_config")

    op.drop_index("ix_yijing_cast_user", table_name="nonebot_plugin_yijing_cast_record")
    op.drop_index("ix_yijing_cast_time", table_name="nonebot_plugin_yijing_cast_record")
    op.drop_index("ix_yijing_cast_question", table_name="nonebot_plugin_yijing_cast_record")
    op.drop_index("ix_yijing_cast_group", table_name="nonebot_plugin_yijing_cast_record")
    op.drop_table("nonebot_plugin_yijing_cast_record")
