from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def trigrams() -> list[dict[str, Any]]:
    return load_json("trigrams.json")


@lru_cache(maxsize=1)
def hexagrams() -> list[dict[str, Any]]:
    return load_json("hexagrams.json")


@lru_cache(maxsize=1)
def guaci() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): i for i in load_json("guaci.json")}


@lru_cache(maxsize=1)
def yaoci() -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(i["hexagram_seq"]), int(i["position"])): i for i in load_json("yaoci.json")}


@lru_cache(maxsize=1)
def xiang() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): i for i in load_json("xiang.json")}


@lru_cache(maxsize=1)
def relations() -> list[dict[str, Any]]:
    return load_json("relations.json")


@lru_cache(maxsize=1)
def sources() -> list[dict[str, Any]]:
    return load_json("sources.json")


@lru_cache(maxsize=1)
def hexagram_by_seq() -> dict[int, dict[str, Any]]:
    return {int(h["seq"]): h for h in hexagrams()}


@lru_cache(maxsize=1)
def hexagram_by_name() -> dict[str, dict[str, Any]]:
    return {h["name"]: h for h in hexagrams()}


@lru_cache(maxsize=1)
def hexagram_by_bits() -> dict[str, dict[str, Any]]:
    return {h["binary_bottom_up"]: h for h in hexagrams()}


def get_hexagram(seq: int) -> dict[str, Any]:
    return hexagram_by_seq()[seq]


def get_hexagram_text(seq: int) -> dict[str, Any]:
    return {
        "hexagram": get_hexagram(seq),
        "guaci": guaci().get(seq, {"text": "卦辞待补录。"}),
        "xiang": xiang().get(seq, {"daxiang": "象传待补录。"}),
        "yaoci": [yaoci().get((seq, pos), {"text": "爻辞待补录。"}) for pos in range(1, 7)],
    }


def find_hexagram(query: str) -> dict[str, Any] | None:
    q = query.strip()
    if not q:
        return None
    if q.isdigit():
        return hexagram_by_seq().get(int(q))
    by_name = hexagram_by_name()
    if q in by_name:
        return by_name[q]
    for h in hexagrams():
        if q in {h["name"], h["palace_name"], h["symbol"], h["unicode_codepoint"]}:
            return h
    for h in hexagrams():
        if q in h["name"] or q in h["palace_name"] or h["name"] in q or h["palace_name"] in q:
            return h
    return None
