from __future__ import annotations

from collections import Counter

from nonebot_plugin_yijing.core.data import load_json


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
