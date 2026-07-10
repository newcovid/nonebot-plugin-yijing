from __future__ import annotations

from copy import deepcopy

import pytest

from nonebot_plugin_yijing.core.manual import advance_manual_coin, advance_manual_yarrow


def test_invalid_coin_input_does_not_mutate_session() -> None:
    state = {"stage": "coin_line", "line": 1, "coins": [], "values": []}
    before = deepcopy(state)

    with pytest.raises(ValueError):
        advance_manual_coin(state, "正反")

    assert state == before


def test_coin_session_advances_six_lines_and_keeps_trace_inputs() -> None:
    state = {"stage": "coin_line", "line": 1, "coins": [], "values": []}
    last = None
    for position in range(1, 7):
        last = advance_manual_coin(state, "正反正")
        state = last.state
        assert last.accepted["position"] == position

    assert last is not None and last.completed is True
    assert state["values"] == [8, 8, 8, 8, 8, 8]
    assert state["coins"] == [["正", "反", "正"]] * 6


def test_invalid_yarrow_input_does_not_mutate_session() -> None:
    state = {
        "stage": "yarrow_change",
        "line": 1,
        "change": 1,
        "current_total": 49,
        "values": [],
        "yarrow_lines": [],
    }
    before = deepcopy(state)

    with pytest.raises(ValueError):
        advance_manual_yarrow(state, "20 20")

    assert state == before


def test_yarrow_session_advances_all_eighteen_changes() -> None:
    state = {
        "stage": "yarrow_change",
        "line": 1,
        "change": 1,
        "current_total": 49,
        "values": [],
        "yarrow_lines": [],
    }
    last = None
    for _line in range(6):
        for split in ("24 25", "20 20", "16 16"):
            last = advance_manual_yarrow(state, split)
            state = last.state

    assert last is not None and last.completed is True
    assert state["values"] == [6, 6, 6, 6, 6, 6]
    assert len(state["yarrow_lines"]) == 6
    assert all(len(item["changes"]) == 3 for item in state["yarrow_lines"])
