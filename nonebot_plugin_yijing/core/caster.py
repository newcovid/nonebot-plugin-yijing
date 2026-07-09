from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from ..config import plugin_config

LineValue = Literal[6, 7, 8, 9]


@dataclass(frozen=True)
class CastResult:
    method: str
    line_values: list[int]
    coins: list[list[str]]
    created_at: datetime
    trace: dict[str, Any] | None = None


@dataclass(frozen=True)
class YarrowChangeResult:
    line_number: int
    change_number: int
    total_before: int
    left: int
    right: int
    removed: int
    total_after: int
    detail: dict[str, int]


def line_to_bit(value: int) -> int:
    if value in (7, 9):
        return 1
    return 0


def changed_line_to_bit(value: int) -> int:
    if value == 6:
        return 1
    if value == 9:
        return 0
    return line_to_bit(value)


def moving_positions(values: list[int]) -> list[int]:
    return [i + 1 for i, v in enumerate(values) if v in (6, 9)]


def cast_coin(rng: random.Random | None = None) -> CastResult:
    rng = rng or random.Random()
    pos = plugin_config.yijing_positive_face
    neg = plugin_config.yijing_negative_face
    p_val = plugin_config.yijing_positive_value
    n_val = plugin_config.yijing_negative_value
    line_values: list[int] = []
    coins: list[list[str]] = []
    line_trace: list[dict[str, Any]] = []
    for _ in range(6):
        faces = [rng.choice([pos, neg]) for _ in range(3)]
        total = sum(p_val if face == pos else n_val for face in faces)
        if total not in (6, 7, 8, 9):
            # 用户若把正反数值改坏，降级到传统 coin 分布。
            total = rng.choice([6, 7, 7, 7, 8, 8, 8, 9])
        coins.append(faces)
        line_values.append(total)
        line_trace.append({"faces": faces, "value": total})
    return CastResult(
        "coin",
        line_values,
        coins,
        datetime.now(timezone.utc),
        {"kind": "coin", "lines_bottom_up": line_trace},
    )


def cast_yarrow(rng: random.Random | None = None) -> CastResult:
    """大衍筮法结果概率模拟。

    传统蓍草法结果概率约为：老阴6=1/16，少阳7=5/16，少阴8=7/16，老阳9=3/16。
    """

    rng = rng or random.Random()
    population = [6] + [7] * 5 + [8] * 7 + [9] * 3
    values = [rng.choice(population) for _ in range(6)]
    return CastResult(
        "yarrow",
        values,
        [],
        datetime.now(timezone.utc),
        {
            "kind": "yarrow_probability",
            "note": "按传统大衍筮法结果概率模拟，不记录十八变实操过程。",
            "lines_bottom_up": [{"value": value} for value in values],
        },
    )


def cast_random_hexagram(rng: random.Random | None = None) -> CastResult:
    rng = rng or random.Random()
    method = rng.choice(["coin", "yarrow"])
    return cast_coin(rng) if method == "coin" else cast_yarrow(rng)


def parse_manual_coin(text: str) -> list[int]:
    """解析六组正反输入。支持：正反正 反反正 ..."""

    pos = plugin_config.yijing_positive_face
    neg = plugin_config.yijing_negative_face
    p_val = plugin_config.yijing_positive_value
    n_val = plugin_config.yijing_negative_value
    groups = [g for g in text.replace("，", " ").replace(",", " ").split() if g]
    if len(groups) != 6:
        raise ValueError("需要自下而上输入 6 组，每组 3 个正/反。")
    values: list[int] = []
    for group in groups:
        faces = list(group)
        if len(faces) != 3 or any(f not in {pos, neg} for f in faces):
            raise ValueError(f"每组必须是 3 个“{pos}/{neg}”，例如：{pos}{neg}{pos}")
        values.append(sum(p_val if face == pos else n_val for face in faces))
    if any(v not in (6, 7, 8, 9) for v in values):
        raise ValueError("正反数值配置错误，无法得到 6/7/8/9 四种爻值。")
    return values


def parse_manual_coin_line(text: str) -> tuple[int, list[str]]:
    pos = plugin_config.yijing_positive_face
    neg = plugin_config.yijing_negative_face
    p_val = plugin_config.yijing_positive_value
    n_val = plugin_config.yijing_negative_value
    group = text.strip().replace("，", "").replace(",", "")
    faces = list(group)
    if len(faces) != 3 or any(face not in {pos, neg} for face in faces):
        raise ValueError(f"每爻必须输入 3 个“{pos}/{neg}”，例如：{pos}{neg}{pos}")
    value = sum(p_val if face == pos else n_val for face in faces)
    if value not in (6, 7, 8, 9):
        raise ValueError("正反数值配置错误，无法得到 6/7/8/9 四种爻值。")
    return value, faces


def parse_manual_yarrow(text: str) -> list[int]:
    parts = [p for p in text.replace("，", " ").replace(",", " ").split() if p]
    if len(parts) != 6:
        raise ValueError("需要自下而上输入 6 个爻值：6/7/8/9。")
    values = [int(p) for p in parts]
    if any(v not in (6, 7, 8, 9) for v in values):
        raise ValueError("爻值只能是 6、7、8、9。")
    return values


def calculate_yarrow_change(
    *,
    line_number: int,
    change_number: int,
    total_before: int,
    left: int,
    right: int,
) -> YarrowChangeResult:
    if line_number < 1 or line_number > 6:
        raise ValueError("爻序必须在 1 到 6 之间。")
    if change_number < 1 or change_number > 3:
        raise ValueError("每爻只有三变。")
    if left <= 0 or right <= 0:
        raise ValueError("左右两堆都必须大于 0。")
    if left + right != total_before:
        raise ValueError(f"左右两堆合计必须为 {total_before}。")

    held = 1
    right_after_hold = right - held
    if right_after_hold < 0:
        raise ValueError("右堆至少需要 1 根用于挂一。")

    left_remainder = left % 4 or 4
    right_remainder = right_after_hold % 4 or 4
    removed = held + left_remainder + right_remainder
    if change_number == 1 and removed not in {5, 9}:
        raise ValueError("第一变归奇结果必须为 5 或 9，请检查分堆数量。")
    if change_number in {2, 3} and removed not in {4, 8}:
        raise ValueError("第二、三变归奇结果必须为 4 或 8，请检查分堆数量。")

    total_after = total_before - removed
    if total_after <= 0 or total_after % 4 != 0:
        raise ValueError("本变后的策数必须为正且可被 4 整除。")

    return YarrowChangeResult(
        line_number=line_number,
        change_number=change_number,
        total_before=total_before,
        left=left,
        right=right,
        removed=removed,
        total_after=total_after,
        detail={
            "held": held,
            "right_after_hold": right_after_hold,
            "left_remainder": left_remainder,
            "right_remainder": right_remainder,
        },
    )


def yarrow_line_value(total_after_three_changes: int) -> int:
    if total_after_three_changes not in {24, 28, 32, 36}:
        raise ValueError("三变后的策数必须是 24、28、32 或 36。")
    return total_after_three_changes // 4
