from __future__ import annotations

from itertools import product

from nonebot_plugin_yijing.core.hexagram import changed_hexagram_from_values, resolve_by_lines


def test_static_qian_resolves_without_changed_hexagram() -> None:
    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])

    assert resolved.primary["name"] == "乾"
    assert resolved.primary_bits == [1, 1, 1, 1, 1, 1]
    assert resolved.changed is None
    assert resolved.moving_positions == []


def test_static_kun_resolves_without_changed_hexagram() -> None:
    resolved = resolve_by_lines([8, 8, 8, 8, 8, 8])

    assert resolved.primary["name"] == "坤"
    assert resolved.primary_bits == [0, 0, 0, 0, 0, 0]
    assert resolved.changed is None
    assert resolved.moving_positions == []


def test_moving_line_generates_changed_hexagram() -> None:
    resolved = resolve_by_lines([9, 7, 7, 7, 7, 7])

    assert resolved.primary["name"] == "乾"
    assert resolved.changed is not None
    assert resolved.changed_bits == [0, 1, 1, 1, 1, 1]
    assert resolved.moving_positions == [1]


def test_invalid_line_values_are_rejected() -> None:
    try:
        resolve_by_lines([7, 8, 9])
    except ValueError as exc:
        assert "长度为 6" in str(exc)
    else:
        raise AssertionError("resolve_by_lines should reject non-six-line input")


def test_dynamic_changed_hexagram_rule_covers_all_line_value_combinations() -> None:
    for values in product([6, 7, 8, 9], repeat=6):
        resolved = resolve_by_lines(list(values))
        changed = changed_hexagram_from_values(list(values))

        assert changed == resolved.changed
