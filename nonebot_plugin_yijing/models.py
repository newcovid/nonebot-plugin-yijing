from __future__ import annotations

from datetime import datetime

from nonebot_plugin_orm import Model
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class CastRecord(Model):
    """起卦/解卦历史记录。"""

    __tablename__ = "nonebot_plugin_yijing_cast_record"
    __table_args__ = (
        Index("ix_yijing_cast_group", "group_id"),
        Index("ix_yijing_cast_user", "user_id_hash"),
        Index("ix_yijing_cast_question", "question_hash"),
        Index("ix_yijing_cast_time", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    adapter: Mapped[str] = mapped_column(String(64), default="")
    bot_id: Mapped[str] = mapped_column(String(128), default="")
    group_id: Mapped[str] = mapped_column(String(128), default="private")
    user_id_hash: Mapped[str] = mapped_column(String(128))
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_norm: Mapped[str] = mapped_column(Text, default="")
    question_hash: Mapped[str] = mapped_column(String(128), default="")
    method: Mapped[str] = mapped_column(String(32))
    coins_json: Mapped[str] = mapped_column(Text, default="[]")
    line_values_json: Mapped[str] = mapped_column(Text)
    moving_positions_json: Mapped[str] = mapped_column(Text, default="[]")
    primary_seq: Mapped[int] = mapped_column(Integer)
    changed_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preprocess_json: Mapped[str] = mapped_column(Text, default="{}")
    interpretation_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GroupConfig(Model):
    """群级配置。"""

    __tablename__ = "nonebot_plugin_yijing_group_config"

    group_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_method: Mapped[str] = mapped_column(String(32), default="coin")
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60)
    daily_limit: Mapped[int] = mapped_column(Integer, default=10)
    duplicate_window_minutes: Mapped[int] = mapped_column(Integer, default=30)
    history_minutes_for_llm: Mapped[int] = mapped_column(Integer, default=120)
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RuntimeQuota(Model):
    """本插件自带的轻量限额记录；更细粒度权限由 access-control 管理。"""

    __tablename__ = "nonebot_plugin_yijing_runtime_quota"
    __table_args__ = (
        Index("ix_yijing_quota_group", "group_id"),
        Index("ix_yijing_quota_user", "user_id_hash"),
        Index("ix_yijing_quota_time", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String(128))
    user_id_hash: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64), default="cast")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GroupCooldown(Model):
    """群级冷却记录。"""

    __tablename__ = "nonebot_plugin_yijing_group_cooldown"

    group_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    last_cast_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_record_id: Mapped[str] = mapped_column(String(32), default="")
    last_user_hash: Mapped[str] = mapped_column(String(128), default="")
    last_question_norm: Mapped[str] = mapped_column(Text, default="")
