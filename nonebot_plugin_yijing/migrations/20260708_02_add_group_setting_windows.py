"""add group setting windows

迁移 ID: 20260708_02
父迁移: 20260708_01
创建时间: 2026-07-08 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_02"
down_revision: str | Sequence[str] | None = "20260708_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "nonebot_plugin_yijing_group_config",
        sa.Column(
            "duplicate_window_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )
    op.add_column(
        "nonebot_plugin_yijing_group_config",
        sa.Column(
            "history_minutes_for_llm",
            sa.Integer(),
            nullable=False,
            server_default="120",
        ),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("nonebot_plugin_yijing_group_config", "history_minutes_for_llm")
    op.drop_column("nonebot_plugin_yijing_group_config", "duplicate_window_minutes")
