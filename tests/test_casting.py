from __future__ import annotations

import random

import pytest

from nonebot_plugin_yijing.core.caster import (
    calculate_yarrow_change,
    cast_coin,
    cast_yarrow,
    parse_manual_coin_line,
    parse_manual_coin,
    parse_manual_yarrow,
    yarrow_line_value,
)


VALID_LINE_VALUES = {6, 7, 8, 9}


def test_coin_cast_returns_six_valid_lines() -> None:
    result = cast_coin(random.Random(1))

    assert result.method == "coin"
    assert len(result.line_values) == 6
    assert set(result.line_values) <= VALID_LINE_VALUES
    assert len(result.coins) == 6
    assert all(len(group) == 3 for group in result.coins)


def test_yarrow_cast_returns_six_valid_lines() -> None:
    result = cast_yarrow(random.Random(1))

    assert result.method == "yarrow"
    assert len(result.line_values) == 6
    assert set(result.line_values) <= VALID_LINE_VALUES
    assert result.coins == []


def test_manual_coin_accepts_only_positive_negative_faces() -> None:
    values = parse_manual_coin("正反正 反反正 正正反 正反反 反正正 反反反")

    assert values == [8, 7, 8, 7, 8, 6]


def test_manual_coin_line_parser_accepts_one_line() -> None:
    value, faces = parse_manual_coin_line("正反正")

    assert value == 8
    assert faces == ["正", "反", "正"]


@pytest.mark.parametrize(
    "text",
    [
        "正反正 反反正",
        "正反正 反反正 正正反 正反反 反正正 正反X",
        "正反 正反正 正正反 正反反 反正正 反反反",
    ],
)
def test_manual_coin_rejects_malformed_input(text: str) -> None:
    with pytest.raises(ValueError):
        parse_manual_coin(text)


def test_manual_yarrow_parser_accepts_valid_values() -> None:
    assert parse_manual_yarrow("7 8 9 6 7 8") == [7, 8, 9, 6, 7, 8]


@pytest.mark.parametrize("text", ["7 8 9", "7 8 9 6 7 10", "7 8 9 6 7 x"])
def test_manual_yarrow_parser_rejects_malformed_values(text: str) -> None:
    with pytest.raises(ValueError):
        parse_manual_yarrow(text)


def test_manual_yarrow_change_calculation_validates_traditional_remainders() -> None:
    first = calculate_yarrow_change(
        line_number=1,
        change_number=1,
        total_before=49,
        left=24,
        right=25,
    )
    second = calculate_yarrow_change(
        line_number=1,
        change_number=2,
        total_before=first.total_after,
        left=20,
        right=20,
    )
    third = calculate_yarrow_change(
        line_number=1,
        change_number=3,
        total_before=second.total_after,
        left=16,
        right=16,
    )

    assert first.removed == 9
    assert second.removed == 8
    assert third.removed == 8
    assert third.total_after == 24
    assert yarrow_line_value(third.total_after) == 6


def test_manual_yarrow_change_rejects_invalid_split_total() -> None:
    with pytest.raises(ValueError, match="合计必须为 49"):
        calculate_yarrow_change(
            line_number=1,
            change_number=1,
            total_before=49,
            left=20,
            right=20,
        )
