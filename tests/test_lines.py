from __future__ import annotations

from collections import Counter

from nonebot_plugin_yijing.core.data import load_json
from nonebot_plugin_yijing.core.hexagram import line_label


def test_line_slots_cover_all_hexagrams_and_positions() -> None:
    lines = load_json("lines.json")

    assert len(lines) == 384
    assert sorted({int(item["hexagram_seq"]) for item in lines}) == list(range(1, 65))

    counter = Counter(int(item["hexagram_seq"]) for item in lines)
    assert all(counter[seq] == 6 for seq in range(1, 65))
    assert all(1 <= int(item["position"]) <= 6 for item in lines)


def test_line_slots_are_unique() -> None:
    lines = load_json("lines.json")
    keys = [(int(item["hexagram_seq"]), int(item["position"])) for item in lines]

    assert len(keys) == len(set(keys)) == 384


def test_line_slot_labels_use_canonical_order() -> None:
    lines = load_json("lines.json")

    assert all(item["label"] == item["line_label"] for item in lines)
    assert line_label(1, 1) == "初九"
    assert line_label(2, 1) == "九二"
    assert line_label(5, 0) == "六五"
    assert line_label(6, 0) == "上六"
