"""add cast trace

迁移 ID: 20260709_01
父迁移: 20260708_02
创建时间: 2026-07-09 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_01"
down_revision: str | Sequence[str] | None = "20260708_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return

    op.add_column(
        "nonebot_plugin_yijing_cast_record",
        sa.Column("cast_trace_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade(name: str = "") -> None:
    if name:
        return

    op.drop_column("nonebot_plugin_yijing_cast_record", "cast_trace_json")
