from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from ..config import plugin_config

LineValue = Literal[6, 7, 8, 9]


@dataclass(frozen=True)
class CastResult:
    method: str
    line_values: list[int]
    coins: list[list[str]]
    created_at: datetime


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
    for _ in range(6):
        faces = [rng.choice([pos, neg]) for _ in range(3)]
        total = sum(p_val if face == pos else n_val for face in faces)
        if total not in (6, 7, 8, 9):
            # 用户若把正反数值改坏，降级到传统 coin 分布。
            total = rng.choice([6, 7, 7, 7, 8, 8, 8, 9])
        coins.append(faces)
        line_values.append(total)
    return CastResult("coin", line_values, coins, datetime.now(timezone.utc))


def cast_yarrow(rng: random.Random | None = None) -> CastResult:
    """大衍筮法结果概率模拟。

    传统蓍草法结果概率约为：老阴6=1/16，少阳7=5/16，少阴8=7/16，老阳9=3/16。
    """

    rng = rng or random.Random()
    population = [6] + [7] * 5 + [8] * 7 + [9] * 3
    return CastResult("yarrow", [rng.choice(population) for _ in range(6)], [], datetime.now(timezone.utc))


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


def parse_manual_yarrow(text: str) -> list[int]:
    parts = [p for p in text.replace("，", " ").replace(",", " ").split() if p]
    if len(parts) != 6:
        raise ValueError("需要自下而上输入 6 个爻值：6/7/8/9。")
    values = [int(p) for p in parts]
    if any(v not in (6, 7, 8, 9) for v in values):
        raise ValueError("爻值只能是 6、7、8、9。")
    return values
