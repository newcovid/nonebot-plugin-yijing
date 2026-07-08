from __future__ import annotations

from nonebot_plugin_yijing.core.data import find_hexagram, hexagrams


def test_hexagram_count_and_sequence_are_complete() -> None:
    items = hexagrams()

    assert len(items) == 64
    assert sorted(int(item["seq"]) for item in items) == list(range(1, 65))


def test_hexagram_names_are_unique() -> None:
    names = [item["name"] for item in hexagrams()]

    assert len(names) == len(set(names))


def test_hexagram_lookup_by_name_and_sequence() -> None:
    by_name = find_hexagram("需")
    by_seq = find_hexagram("5")

    assert by_name is not None
    assert by_seq is not None
    assert by_name["seq"] == 5
    assert by_seq["name"] == "需"


def test_hexagram_binary_keys_are_six_bits_and_unique() -> None:
    keys = [item["binary_bottom_up"] for item in hexagrams()]

    assert len(keys) == len(set(keys)) == 64
    assert all(len(key) == 6 and set(key) <= {"0", "1"} for key in keys)
