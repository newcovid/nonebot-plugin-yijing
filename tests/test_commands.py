from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from nonebot_plugin_yijing.commands import main as command_main
from nonebot_plugin_yijing.commands.main import (
    HELP_COMMANDS,
    _manual_expired,
    _manual_key,
    _parse_cast_body,
    _parse_history_cleanup_target,
    _parse_yarrow_split,
    _set_group_llm_enabled,
)
from nonebot_plugin_yijing.models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota
from nonebot_plugin_yijing.utils import hash_text, hash_user_id, normalize_question
from nonebot_plugin_yijing.utils import get_group_id


@dataclass
class FakeBot:
    type: str = "Discord"
    self_id: str = "10000"


@dataclass
class FakeEvent:
    group_id: str = "20000"
    user_id: str = "30000"

    def get_user_id(self) -> str:
        return self.user_id


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("项目是否顺利", ("项目是否顺利", "default", False)),
        ("项目是否顺利 铜钱", ("项目是否顺利", "coin", False)),
        ("项目是否顺利 大衍", ("项目是否顺利", "yarrow", False)),
        ("项目是否顺利 手动", ("项目是否顺利", "manual", False)),
        ("项目是否顺利 --force 铜钱", ("项目是否顺利", "coin", True)),
        ("项目是否顺利 手动 --force", ("项目是否顺利", "manual", True)),
    ],
)
def test_parse_cast_body_distinguishes_default_and_explicit_methods(
    body: str, expected: tuple[str, str, bool]
) -> None:
    assert _parse_cast_body(body) == expected


def test_manual_key_isolated_by_bot_group_and_user() -> None:
    assert _manual_key(FakeBot(), FakeEvent()) == (
        "Discord",
        "10000",
        get_group_id(FakeEvent()),
        "30000",
    )
    assert _manual_key(FakeBot(self_id="10001"), FakeEvent()) != _manual_key(
        FakeBot(), FakeEvent()
    )
    assert _manual_key(FakeBot(), FakeEvent(user_id="30001")) != _manual_key(
        FakeBot(), FakeEvent()
    )


def test_help_nests_every_settings_subcommand() -> None:
    settings = next(item for item in HELP_COMMANDS if item["cmd"] == "易经设置")
    assert not any(item["cmd"].startswith("易经设置 ") for item in HELP_COMMANDS)
    assert [item["cmd"] for item in settings["children"]] == [
        "开启 / 关闭",
        "冷却 秒数",
        "日限额 次数",
        "重复窗口 分钟",
        "历史窗口 分钟",
        "默认 铜钱 / 大衍",
        "LLM 开启 / 关闭",
    ]


def test_generic_session_id_is_used_when_adapter_has_no_group_fields() -> None:
    class SessionEvent:
        def get_session_id(self) -> str:
            return "channel_42"

        def get_user_id(self) -> str:
            return "user_7"

    context_id = get_group_id(SessionEvent())  # type: ignore[arg-type]
    assert ":session:" in context_id
    assert context_id.endswith(":channel_42")


def test_adapter_namespace_prevents_group_id_collisions() -> None:
    class AdapterAEvent(FakeEvent):
        pass

    class AdapterBEvent(FakeEvent):
        pass

    AdapterAEvent.__module__ = "nonebot.adapters.adapter_a.event"
    AdapterBEvent.__module__ = "nonebot.adapters.adapter_b.event"

    assert get_group_id(AdapterAEvent()) == "adapter_a:group:20000"
    assert get_group_id(AdapterBEvent()) == "adapter_b:group:20000"


def test_onebot_group_key_remains_backward_compatible() -> None:
    class OneBotEvent(FakeEvent):
        pass

    OneBotEvent.__module__ = "nonebot.adapters.onebot.v11.event"

    assert get_group_id(OneBotEvent()) == "20000"


def test_parse_yarrow_split_accepts_two_integer_piles() -> None:
    assert _parse_yarrow_split("24 25") == (24, 25)
    assert _parse_yarrow_split("24，25") == (24, 25)


@pytest.mark.parametrize("text", ["24", "24 20 5", "左 右"])
def test_parse_yarrow_split_rejects_malformed_input(text: str) -> None:
    with pytest.raises(ValueError):
        _parse_yarrow_split(text)


def test_manual_expired_uses_updated_at_timestamp() -> None:
    assert _manual_expired({"updated_at": 0}) is True


def test_llm_privacy_notice_is_only_shown_on_first_enable() -> None:
    cfg = SimpleNamespace(llm_enabled=False, llm_privacy_notice_shown=False)

    assert _set_group_llm_enabled(cfg, True) is True
    assert cfg.llm_enabled is True
    assert cfg.llm_privacy_notice_shown is True
    assert _set_group_llm_enabled(cfg, False) is False
    assert _set_group_llm_enabled(cfg, True) is False


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("YJ-ABC12345", "YJ-ABC12345"),
        ("yj-abc12345", "YJ-ABC12345"),
        ("全部", None),
        ("全量", None),
        ("all", None),
    ],
)
def test_parse_history_cleanup_target(body: str, expected: str | None) -> None:
    assert _parse_history_cleanup_target(body) == expected


@pytest.mark.parametrize("body", ["", "ABC12345", "YJ-ABC-123"])
def test_parse_history_cleanup_target_rejects_invalid_input(body: str) -> None:
    with pytest.raises(ValueError):
        _parse_history_cleanup_target(body)


@pytest.mark.asyncio
async def test_duplicate_record_is_rendered_without_llm_or_new_record(
    monkeypatch: pytest.MonkeyPatch,
    test_database_url: str,
) -> None:
    engine = create_async_engine(test_database_url)
    async with engine.begin() as connection:
        for table in (CastRecord, GroupConfig, GroupCooldown, RuntimeQuota):
            await connection.run_sync(table.__table__.drop, checkfirst=True)
        for table in (CastRecord, GroupConfig, GroupCooldown, RuntimeQuota):
            await connection.run_sync(table.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    event = FakeEvent()
    question = "项目是否顺利"
    rendered: dict[str, Any] = {}
    llm_called = False

    async def _capture_finish(matcher: Any, template: str, data: dict[str, Any]) -> None:
        rendered.update({"template": template, "data": data})

    async def _unexpected_preprocess(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal llm_called
        llm_called = bool(args or kwargs)
        return {}

    monkeypatch.setattr(command_main, "_finish_template", _capture_finish)
    monkeypatch.setattr(command_main, "preprocess_question", _unexpected_preprocess)
    async with factory() as session:
        group_id = get_group_id(event)
        user_hash = hash_user_id(event.get_user_id())
        normalized = normalize_question(question)
        session.add(
            CastRecord(
                id="YJ-OLD00001",
                adapter="test",
                bot_id="10000",
                group_id=group_id,
                user_id_hash=user_hash,
                question_text=question,
                question_norm=normalized,
                question_hash=hash_text(normalized),
                method="coin",
                coins_json='[["A", "B", "A"]]',
                line_values_json="[7, 7, 7, 7, 7, 7]",
                moving_positions_json="[]",
                cast_trace_json='{"kind": "coin"}',
                primary_seq=1,
                changed_seq=None,
                preprocess_json='{"allowed": true}',
                interpretation_json='{"summary": "旧记录", "advice": ["旧建议"]}',
                created_at=datetime.now(),
            )
        )
        await session.commit()

        await command_main._run_cast(
            matcher=SimpleNamespace(),
            bot=FakeBot(),
            event=event,
            session=session,
            question=question,
            method="coin",
        )

        count = await session.scalar(select(func.count()).select_from(CastRecord))
        reused_record_id = rendered["data"]["record_id"]
        reused_coins = rendered["data"]["coins"]

        async def _local_preprocess(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return command_main.local_preprocess(question, [])

        monkeypatch.setattr(command_main, "preprocess_question", _local_preprocess)
        await command_main._run_cast(
            matcher=SimpleNamespace(),
            bot=FakeBot(),
            event=event,
            session=session,
            question=question,
            method="coin",
            force_recast=True,
        )
        forced_count = await session.scalar(select(func.count()).select_from(CastRecord))

    async with engine.begin() as connection:
        for table in reversed((CastRecord, GroupConfig, GroupCooldown, RuntimeQuota)):
            await connection.run_sync(table.__table__.drop, checkfirst=True)
    await engine.dispose()
    assert llm_called is False
    assert count == 1
    assert forced_count == 2
    assert rendered["template"] == "card.html"
    assert reused_record_id == "YJ-OLD00001"
    assert reused_coins == [["正", "反", "正"]]
