from __future__ import annotations

from dataclasses import dataclass

import pytest

from nonebot_plugin_yijing.commands.main import (
    _manual_expired,
    _manual_key,
    _parse_cast_body,
    _parse_yarrow_split,
)


@dataclass
class FakeBot:
    type: str = "OneBot V11"
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
    assert _manual_key(FakeBot(), FakeEvent()) == ("OneBot V11", "10000", "20000", "30000")
    assert _manual_key(FakeBot(self_id="10001"), FakeEvent()) != _manual_key(
        FakeBot(), FakeEvent()
    )
    assert _manual_key(FakeBot(), FakeEvent(user_id="30001")) != _manual_key(
        FakeBot(), FakeEvent()
    )


def test_parse_yarrow_split_accepts_two_integer_piles() -> None:
    assert _parse_yarrow_split("24 25") == (24, 25)
    assert _parse_yarrow_split("24，25") == (24, 25)


@pytest.mark.parametrize("text", ["24", "24 20 5", "左 右"])
def test_parse_yarrow_split_rejects_malformed_input(text: str) -> None:
    with pytest.raises(ValueError):
        _parse_yarrow_split(text)


def test_manual_expired_uses_updated_at_timestamp() -> None:
    assert _manual_expired({"updated_at": 0}) is True
