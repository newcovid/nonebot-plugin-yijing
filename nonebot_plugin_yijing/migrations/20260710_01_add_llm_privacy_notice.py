"""add llm privacy notice state

迁移 ID: 20260710_01
父迁移: 20260709_01
创建时间: 2026-07-10 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260710_01"
down_revision: str | Sequence[str] | None = "20260709_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "nonebot_plugin_yijing_group_config",
        sa.Column(
            "llm_privacy_notice_shown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("nonebot_plugin_yijing_group_config", "llm_privacy_notice_shown")
