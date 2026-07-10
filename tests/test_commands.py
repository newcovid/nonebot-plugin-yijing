from __future__ import annotations

from dataclasses import dataclass

import pytest

from nonebot_plugin_yijing.commands.main import (
    HELP_COMMANDS,
    _manual_expired,
    _manual_key,
    _parse_cast_body,
    _parse_history_cleanup_target,
    _parse_yarrow_split,
)
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
        ("项目是否顺利", ("项目是否顺利", "default")),
        ("项目是否顺利 铜钱", ("项目是否顺利", "coin")),
        ("项目是否顺利 大衍", ("项目是否顺利", "yarrow")),
        ("项目是否顺利 手动", ("项目是否顺利", "manual")),
    ],
)
def test_parse_cast_body_distinguishes_default_and_explicit_methods(
    body: str, expected: tuple[str, str]
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
