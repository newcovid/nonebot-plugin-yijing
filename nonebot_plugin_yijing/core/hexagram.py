from __future__ import annotations

from dataclasses import dataclass

from .caster import changed_line_to_bit, line_to_bit, moving_positions
from .data import get_hexagram, hexagram_by_bits


@dataclass(frozen=True)
class ResolvedHexagram:
    line_values: list[int]
    primary_bits: list[int]
    changed_bits: list[int]
    moving_positions: list[int]
    primary: dict
    changed: dict | None


def resolve_by_lines(values: list[int]) -> ResolvedHexagram:
    if len(values) != 6 or any(v not in (6, 7, 8, 9) for v in values):
        raise ValueError("六爻值必须是长度为 6 的 6/7/8/9 列表。")
    primary_bits = [line_to_bit(v) for v in values]
    changed_bits = [changed_line_to_bit(v) for v in values]
    by_bits = hexagram_by_bits()
    p_key = "".join(map(str, primary_bits))
    c_key = "".join(map(str, changed_bits))
    primary = by_bits[p_key]
    changed = by_bits[c_key] if c_key != p_key else None
    return ResolvedHexagram(values, primary_bits, changed_bits, moving_positions(values), primary, changed)


def resolve_static_hexagram(seq: int) -> ResolvedHexagram:
    h = get_hexagram(seq)
    bits = list(h["bits_bottom_up"])
    values = [7 if bit else 8 for bit in bits]
    return ResolvedHexagram(values, bits, bits, [], h, None)


def line_label(position: int, bit: int) -> str:
    pos_name = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}[position]
    return f"{pos_name}{'九' if bit else '六'}"


def render_line_shape(bit: int, moving: bool = False) -> str:
    base = "━━━━━━" if bit else "━━  ━━"
    return f"{base} {'动' if moving else '静'}"


def changed_hexagram_from_values(values: list[int]) -> dict | None:
    return resolve_by_lines(values).changed
