from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TEXT_STATUSES = {"placeholder", "draft", "seeded", "checked", "verified"}


def load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def trigrams() -> list[dict[str, Any]]:
    return load_json("trigrams.json")


@lru_cache(maxsize=1)
def hexagrams() -> list[dict[str, Any]]:
    return load_json("hexagrams.json")


@lru_cache(maxsize=1)
def lines() -> list[dict[str, Any]]:
    return load_json("lines.json")


@lru_cache(maxsize=1)
def lines_by_hexagram_position() -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(i["hexagram_seq"]), int(i["position"])): i for i in lines()}


@lru_cache(maxsize=1)
def guaci() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): i for i in load_json("guaci.json")}


@lru_cache(maxsize=1)
def yaoci() -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(i["hexagram_seq"]), int(i["position"])): i for i in load_json("yaoci.json")}


def _normalize_xiaoxiang(
    hexagram_seq: int,
    raw_items: Any,
    *,
    source_id: str | None,
    status: str | None,
) -> list[dict[str, Any]]:
    """Return small-image records with a stable list-of-objects shape.

    Early alpha data allowed ``xiaoxiang`` to be an empty list or a mapping such as
    ``{"1": "..."}``. Runtime code normalizes both forms so old seed data does
    not leak schema instability into rendering or LLM prompts.
    """

    if isinstance(raw_items, dict):
        normalized = []
        for key, text in sorted(raw_items.items(), key=lambda item: int(item[0])):
            position = int(key)
            line = lines_by_hexagram_position().get((hexagram_seq, position), {})
            normalized.append(
                {
                    "position": position,
                    "line_label": line.get("line_label", ""),
                    "text": text,
                    "source_id": source_id,
                    "status": status or "placeholder",
                }
            )
        return normalized

    if isinstance(raw_items, list):
        normalized = []
        for item in raw_items:
            if isinstance(item, dict):
                normalized.append(item)
            else:
                normalized.append(
                    {
                        "position": None,
                        "line_label": "",
                        "text": str(item),
                        "source_id": source_id,
                        "status": status or "placeholder",
                    }
                )
        return normalized

    return []


def _normalize_xiang_record(item: dict[str, Any]) -> dict[str, Any]:
    seq = int(item["hexagram_seq"])
    source_id = item.get("daxiang_source_id") or item.get("source_id")
    status = item.get("daxiang_status") or item.get("status")
    normalized = dict(item)
    normalized["xiaoxiang"] = _normalize_xiaoxiang(
        seq,
        item.get("xiaoxiang", []),
        source_id=source_id,
        status=status,
    )
    normalized["xiaoxiang_by_position"] = {
        str(i["position"]): i for i in normalized["xiaoxiang"] if i.get("position") is not None
    }
    return normalized


@lru_cache(maxsize=1)
def xiang() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): _normalize_xiang_record(i) for i in load_json("xiang.json")}


@lru_cache(maxsize=1)
def tuan() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): i for i in load_json("tuan.json")}


@lru_cache(maxsize=1)
def wenyan() -> dict[int, dict[str, Any]]:
    return {int(i["hexagram_seq"]): i for i in load_json("wenyan.json")}


@lru_cache(maxsize=1)
def xici_shang() -> list[dict[str, Any]]:
    return load_json("xici_shang.json")


@lru_cache(maxsize=1)
def xici_xia() -> list[dict[str, Any]]:
    return load_json("xici_xia.json")


@lru_cache(maxsize=1)
def shuogua() -> list[dict[str, Any]]:
    return load_json("shuogua.json")


@lru_cache(maxsize=1)
def xugua() -> list[dict[str, Any]]:
    return load_json("xugua.json")


@lru_cache(maxsize=1)
def zagua() -> list[dict[str, Any]]:
    return load_json("zagua.json")


@lru_cache(maxsize=1)
def special_texts() -> list[dict[str, Any]]:
    return load_json("special_texts.json")


@lru_cache(maxsize=1)
def special_texts_by_hexagram() -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in special_texts():
        grouped.setdefault(int(item["hexagram_seq"]), []).append(item)
    return grouped


@lru_cache(maxsize=1)
def relations() -> list[dict[str, Any]]:
    return load_json("relations.json")


@lru_cache(maxsize=1)
def sources() -> list[dict[str, Any]]:
    return load_json("sources.json")


@lru_cache(maxsize=1)
def casting_rules() -> list[dict[str, Any]]:
    return load_json("casting_rules.json")


@lru_cache(maxsize=1)
def interpret_rules() -> list[dict[str, Any]]:
    return load_json("interpret_rules.json")


@lru_cache(maxsize=1)
def reserved_tables() -> dict[str, Any]:
    return load_json("reserved_tables.json")


@lru_cache(maxsize=1)
def dynasty_commentaries() -> list[dict[str, Any]]:
    return load_json("dynasty_commentaries.json")


@lru_cache(maxsize=1)
def meihua_rules() -> list[dict[str, Any]]:
    return load_json("meihua_rules.json")


@lru_cache(maxsize=1)
def najia_rules() -> list[dict[str, Any]]:
    return load_json("najia_rules.json")


@lru_cache(maxsize=1)
def ganzhi_calendar() -> list[dict[str, Any]]:
    return load_json("ganzhi_calendar.json")


@lru_cache(maxsize=1)
def wuxing_strength() -> list[dict[str, Any]]:
    return load_json("wuxing_strength.json")


@lru_cache(maxsize=1)
def liuqin_liushen() -> list[dict[str, Any]]:
    return load_json("liuqin_liushen.json")


@lru_cache(maxsize=1)
def modern_explanations() -> list[dict[str, Any]]:
    return load_json("modern_explanations.json")


@lru_cache(maxsize=1)
def scenario_templates() -> list[dict[str, Any]]:
    return load_json("scenario_templates.json")


@lru_cache(maxsize=1)
def schema_manifest() -> dict[str, Any]:
    return load_json("schemas/manifest.json")


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
        "guaci": guaci().get(seq, {"text": "卦辞待补录。", "status": "placeholder"}),
        "tuan": tuan().get(seq, {"text": "彖传待补录。", "status": "placeholder"}),
        "xiang": xiang().get(seq, {"daxiang": "象传待补录。", "status": "placeholder"}),
        "wenyan": wenyan().get(seq),
        "special_texts": special_texts_by_hexagram().get(seq, []),
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
