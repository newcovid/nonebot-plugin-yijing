from __future__ import annotations

import json
import secrets
from datetime import timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import plugin_config
from ..models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota
from ..utils import hash_text, normalize_question, text_similarity, utcnow


def new_record_id() -> str:
    return "YJ-" + secrets.token_hex(4).upper()


async def get_or_create_group_config(session: AsyncSession, group_id: str) -> GroupConfig:
    cfg = await session.get(GroupConfig, group_id)
    if cfg is None:
        cfg = GroupConfig(
            group_id=group_id,
            enabled=plugin_config.yijing_group_default_enabled,
            default_method=plugin_config.yijing_default_method,
            cooldown_seconds=plugin_config.yijing_cooldown_seconds,
            daily_limit=plugin_config.yijing_daily_limit_per_user,
            llm_enabled=plugin_config.yijing_llm_enabled,
        )
        session.add(cfg)
        await session.commit()
        await session.refresh(cfg)
    return cfg


async def save_record(
    session: AsyncSession,
    *,
    adapter: str,
    bot_id: str,
    group_id: str,
    user_hash: str,
    question: str | None,
    method: str,
    coins: list[list[str]],
    line_values: list[int],
    moving_positions: list[int],
    primary_seq: int,
    changed_seq: int | None,
    preprocess: dict[str, Any],
    interpretation: dict[str, Any],
) -> CastRecord:
    q_norm = normalize_question(question)
    record = CastRecord(
        id=new_record_id(),
        adapter=adapter,
        bot_id=bot_id,
        group_id=group_id,
        user_id_hash=user_hash,
        question_text=question if plugin_config.yijing_store_question else None,
        question_norm=q_norm,
        question_hash=hash_text(q_norm),
        method=method,
        coins_json=json.dumps(coins, ensure_ascii=False),
        line_values_json=json.dumps(line_values, ensure_ascii=False),
        moving_positions_json=json.dumps(moving_positions, ensure_ascii=False),
        primary_seq=primary_seq,
        changed_seq=changed_seq,
        preprocess_json=json.dumps(preprocess, ensure_ascii=False),
        interpretation_json=json.dumps(interpretation, ensure_ascii=False),
        created_at=utcnow(),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def add_quota(session: AsyncSession, group_id: str, user_hash: str, action: str = "cast") -> None:
    session.add(RuntimeQuota(group_id=group_id, user_id_hash=user_hash, action=action, created_at=utcnow()))
    await session.commit()


async def daily_quota_count(
    session: AsyncSession, group_id: str, user_hash: str, action: str = "cast"
) -> int:
    since = utcnow() - timedelta(hours=24)
    stmt = select(func.count()).select_from(RuntimeQuota).where(
        RuntimeQuota.group_id == group_id,
        RuntimeQuota.user_id_hash == user_hash,
        RuntimeQuota.action == action,
        RuntimeQuota.created_at >= since,
    )
    return int((await session.execute(stmt)).scalar_one())


async def cooldown_remaining(session: AsyncSession, group_id: str, cooldown_seconds: int) -> int:
    if cooldown_seconds <= 0:
        return 0
    cd = await session.get(GroupCooldown, group_id)
    if cd is None:
        return 0
    elapsed = (utcnow() - cd.last_cast_at).total_seconds()
    remain = cooldown_seconds - int(elapsed)
    return max(0, remain)


async def touch_cooldown(
    session: AsyncSession,
    *,
    group_id: str,
    record_id: str,
    user_hash: str,
    question_norm: str,
) -> None:
    cd = await session.get(GroupCooldown, group_id)
    if cd is None:
        cd = GroupCooldown(group_id=group_id)
        session.add(cd)
    cd.last_cast_at = utcnow()
    cd.last_record_id = record_id
    cd.last_user_hash = user_hash
    cd.last_question_norm = question_norm
    await session.commit()


async def get_record(session: AsyncSession, record_id: str) -> CastRecord | None:
    return await session.get(CastRecord, record_id.upper())


def _record_stmt(group_id: str, user_hash: str | None = None) -> Select[tuple[CastRecord]]:
    stmt = select(CastRecord).where(CastRecord.group_id == group_id)
    if user_hash:
        stmt = stmt.where(CastRecord.user_id_hash == user_hash)
    return stmt.order_by(CastRecord.created_at.desc())


async def recent_records(
    session: AsyncSession,
    *,
    group_id: str,
    user_hash: str | None = None,
    limit: int = 10,
    minutes: int | None = None,
) -> list[CastRecord]:
    stmt = _record_stmt(group_id, user_hash).limit(limit)
    if minutes is not None:
        stmt = stmt.where(CastRecord.created_at >= utcnow() - timedelta(minutes=minutes))
    return list((await session.execute(stmt)).scalars().all())


async def all_user_records(
    session: AsyncSession, *, group_id: str, user_hash: str, limit: int = 200
) -> list[CastRecord]:
    stmt = _record_stmt(group_id, user_hash).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def find_similar_recent(
    session: AsyncSession,
    *,
    group_id: str,
    user_hash: str,
    question: str,
    minutes: int,
    threshold: float = 0.72,
) -> tuple[CastRecord, float] | None:
    qn = normalize_question(question)
    if not qn:
        return None
    candidates = await recent_records(
        session, group_id=group_id, user_hash=user_hash, limit=30, minutes=minutes
    )
    best: tuple[CastRecord, float] | None = None
    for record in candidates:
        score = text_similarity(qn, record.question_norm)
        if best is None or score > best[1]:
            best = (record, score)
    if best and best[1] >= threshold:
        return best
    return None


def record_to_dict(record: CastRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "question": record.question_text or "（未保存原问题）",
        "method": record.method,
        "line_values": json.loads(record.line_values_json),
        "moving_positions": json.loads(record.moving_positions_json),
        "primary_seq": record.primary_seq,
        "changed_seq": record.changed_seq,
        "coins": json.loads(record.coins_json),
        "preprocess": json.loads(record.preprocess_json or "{}"),
        "interpretation": json.loads(record.interpretation_json or "{}"),
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
