from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nonebot_plugin_yijing.models import CastRecord
from nonebot_plugin_yijing.services import repository
from nonebot_plugin_yijing.services.repository import delete_user_records, find_similar_recent


@pytest.fixture
async def session(test_database_url: str) -> AsyncSession:
    engine = create_async_engine(test_database_url)
    async with engine.begin() as connection:
        await connection.run_sync(CastRecord.__table__.drop, checkfirst=True)
        await connection.run_sync(CastRecord.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as value:
            yield value
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(CastRecord.__table__.drop, checkfirst=True)
        await engine.dispose()


def _record(
    record_id: str,
    *,
    group_id: str = "group-a",
    user_hash: str = "user-a",
    question: str = "项目是否顺利",
    created_at: datetime | None = None,
) -> CastRecord:
    return CastRecord(
        id=record_id,
        adapter="onebot.v11",
        bot_id="bot",
        group_id=group_id,
        user_id_hash=user_hash,
        question_text=question,
        question_norm=question,
        question_hash="hash",
        method="coin",
        coins_json="[]",
        line_values_json="[7, 7, 7, 7, 7, 7]",
        moving_positions_json="[]",
        cast_trace_json="{}",
        primary_seq=1,
        changed_seq=None,
        preprocess_json="{}",
        interpretation_json="{}",
        created_at=created_at or datetime(2026, 7, 10, 8, 0, 0),
    )


async def test_delete_user_records_is_scoped_to_current_user_and_group(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            _record("YJ-OWN00001"),
            _record("YJ-OWN00002"),
            _record("YJ-OTHER001", user_hash="user-b"),
            _record("YJ-GROUP001", group_id="group-b"),
        ]
    )
    await session.commit()

    assert (
        await delete_user_records(
            session,
            group_id="group-a",
            user_hash="user-a",
            record_id="yj-own00001",
        )
        == 1
    )
    assert await delete_user_records(session, group_id="group-a", user_hash="user-a") == 1

    remaining = set((await session.execute(select(CastRecord.id))).scalars())
    assert remaining == {"YJ-OTHER001", "YJ-GROUP001"}


async def test_similar_question_window_is_measured_in_minutes(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(2026, 7, 10, 8, 0, 0)
    monkeypatch.setattr(repository, "utcnow", lambda: now)
    session.add_all(
        [
            _record("YJ-RECENT01", group_id="recent", created_at=now - timedelta(minutes=29)),
            _record("YJ-OLD00001", group_id="old", created_at=now - timedelta(minutes=31)),
        ]
    )
    await session.commit()

    recent = await find_similar_recent(
        session,
        group_id="recent",
        user_hash="user-a",
        question="项目是否顺利",
        minutes=30,
    )
    old = await find_similar_recent(
        session,
        group_id="old",
        user_hash="user-a",
        question="项目是否顺利",
        minutes=30,
    )

    assert recent is not None
    assert recent[0].id == "YJ-RECENT01"
    assert old is None
