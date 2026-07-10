from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .caster import calculate_yarrow_change, parse_manual_coin_line, yarrow_line_value


@dataclass(frozen=True)
class ManualStepResult:
    state: dict[str, Any]
    accepted: dict[str, Any]
    completed: bool = False
    line_completed: bool = False


def parse_yarrow_split(text: str) -> tuple[int, int]:
    parts = [part for part in text.replace("，", " ").replace(",", " ").split() if part]
    if len(parts) != 2:
        raise ValueError("请只输入左右两堆数量，例如：24 25。")
    try:
        left, right = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError("左右两堆数量必须是整数。") from exc
    return left, right


def advance_manual_coin(state: dict[str, Any], text: str) -> ManualStepResult:
    """Validate one coin line and return a new state without mutating the input."""

    value, faces = parse_manual_coin_line(text)
    next_state = deepcopy(state)
    line = int(next_state["line"])
    next_state.setdefault("coins", []).append(faces)
    next_state.setdefault("values", []).append(value)
    accepted = {"position": line, "faces": faces, "value": value}
    if line < 6:
        next_state["line"] = line + 1
        return ManualStepResult(state=next_state, accepted=accepted)
    return ManualStepResult(
        state=next_state,
        accepted=accepted,
        completed=True,
        line_completed=True,
    )


def advance_manual_yarrow(state: dict[str, Any], text: str) -> ManualStepResult:
    """Validate one yarrow change and return a new state without mutating the input."""

    left, right = parse_yarrow_split(text)
    next_state = deepcopy(state)
    line = int(next_state["line"])
    change = int(next_state["change"])
    result = calculate_yarrow_change(
        line_number=line,
        change_number=change,
        total_before=int(next_state["current_total"]),
        left=left,
        right=right,
    )
    current_line = list(next_state.get("current_line_changes", []))
    change_data = {
        "change": result.change_number,
        "total_before": result.total_before,
        "left": result.left,
        "right": result.right,
        "removed": result.removed,
        "total_after": result.total_after,
        **result.detail,
    }
    current_line.append(change_data)
    next_state["current_line_changes"] = current_line
    next_state["current_total"] = result.total_after
    if change < 3:
        next_state["change"] = change + 1
        return ManualStepResult(state=next_state, accepted=change_data)

    value = yarrow_line_value(result.total_after)
    next_state.setdefault("values", []).append(value)
    next_state.setdefault("yarrow_lines", []).append(
        {"position": line, "value": value, "changes": current_line}
    )
    next_state.pop("current_line_changes", None)
    accepted = {**change_data, "position": line, "value": value}
    if line < 6:
        next_state.update({"line": line + 1, "change": 1, "current_total": 49})
        return ManualStepResult(state=next_state, accepted=accepted, line_completed=True)
    return ManualStepResult(
        state=next_state,
        accepted=accepted,
        completed=True,
        line_completed=True,
    )
