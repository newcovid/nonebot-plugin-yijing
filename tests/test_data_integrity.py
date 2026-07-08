from __future__ import annotations

from nonebot_plugin_yijing.core.data import hexagram_by_seq, relations


VALID_RELATIONS = {"opposite", "inverse", "nuclear"}


def test_every_hexagram_relation_points_to_existing_hexagram() -> None:
    hexagram_seqs = set(hexagram_by_seq())

    for relation in relations():
        source_seq = int(relation["hexagram_seq"])
        target_seq = int(relation["target_seq"])

        assert source_seq in hexagram_seqs
        assert target_seq in hexagram_seqs
        assert relation["relation"] in VALID_RELATIONS
