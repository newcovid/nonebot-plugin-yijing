from __future__ import annotations

from typing import Any

from ..config import plugin_config
from ..core.data import find_hexagram, get_hexagram_text, hexagram_by_seq, sources
from ..core.hexagram import (
    ResolvedHexagram,
    line_label,
    render_line_shape,
    resolve_by_lines,
    resolve_static_hexagram,
)
from ..services.repository import record_to_dict

LINE_NAME = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
LINE_CHANGE = {6: "阴动变阳", 7: "阳静不变", 8: "阴静不变", 9: "阳动变阴"}
METHOD_NAME = {
    "coin": "三枚铜钱法",
    "manual_coin": "手动三枚铜钱法",
    "yarrow": "大衍筮法模拟",
    "manual_yarrow": "手动大衍筮法",
    "random": "随机一卦",
}
INTERPRETATION_SOURCE = {
    "success": "LLM 综合解读",
    "not_requested": "本地规则解读",
    "fallback_config": "LLM 不可用，已安全降级",
    "fallback_request": "LLM 不可用，已安全降级",
    "fallback_invalid": "LLM 不可用，已安全降级",
}


def _display_coin_faces(coins: list[list[str]]) -> list[list[str]]:
    """Convert legacy internal A/B markers to the configured face labels."""

    legacy_labels = {
        "A": plugin_config.yijing_positive_face,
        "B": plugin_config.yijing_negative_face,
    }
    rows: list[list[str]] = []
    for group in coins:
        row = []
        for face in group:
            text = "" if face is None else str(face).strip()
            row.append(legacy_labels.get(text.upper(), text))
        rows.append(row)
    return rows


def _coin_rows(coins: list[list[str]]) -> list[list[dict[str, str]]]:
    return [
        [
            {
                "label": face,
                "side": (
                    "positive"
                    if face == plugin_config.yijing_positive_face
                    else "negative"
                    if face == plugin_config.yijing_negative_face
                    else "neutral"
                ),
            }
            for face in group
        ]
        for group in coins
    ]


def _yaoci_body(item: dict[str, Any], label: str) -> str:
    text = str(item.get("text") or "爻辞待补录。").strip()
    stored_label = str(item.get("line_label") or label)
    for prefix in dict.fromkeys((stored_label, label)):
        if prefix and text.startswith(prefix):
            body = text[len(prefix) :].lstrip(" ：:，,、")
            return body or text
    return text


def _normalize_interpretation(value: dict[str, Any]) -> dict[str, Any]:
    """Read both the v2 interpretation contract and legacy record JSON."""

    result = dict(value or {})
    summary = str(result.get("summary") or "")
    old_advice = result.pop("advice", [])
    advice = result.get("actionable_advice", old_advice)
    if not isinstance(advice, list):
        advice = []
    llm_used = bool(result.get("llm_used", False))
    status = str(result.get("llm_status") or ("success" if llm_used else "not_requested"))
    result.update(
        {
            "schema_version": int(result.get("schema_version") or 1),
            "summary": summary,
            "answer_to_question": str(result.get("answer_to_question") or summary),
            "hexagram_structure": str(
                result.get("hexagram_structure") or result.get("current_situation") or summary
            ),
            "current_situation": str(result.get("current_situation") or summary),
            "changing_line_focus": str(
                result.get("changing_line_focus") or "旧记录未保存独立的动爻重点说明。"
            ),
            "change_trend": str(result.get("change_trend") or ""),
            "actionable_advice": [str(item) for item in advice if str(item).strip()],
            "risks": result.get("risks", []) if isinstance(result.get("risks", []), list) else [],
            "relations": (
                result.get("relations", []) if isinstance(result.get("relations", []), list) else []
            ),
            "disclaimer": str(result.get("disclaimer") or "本结果仅供传统文化学习与反思。"),
            "llm_used": llm_used,
            "llm_status": status,
            "fallback_reason": result.get("fallback_reason"),
            "source_label": INTERPRETATION_SOURCE.get(status, "本地规则解读"),
            "is_fallback": status.startswith("fallback_"),
        }
    )
    return result


def classic_text_for(resolved: ResolvedHexagram) -> dict[str, Any]:
    primary = get_hexagram_text(int(resolved.primary["seq"]))
    changed = get_hexagram_text(int(resolved.changed["seq"])) if resolved.changed else None
    return {"primary": primary, "changed": changed}


def build_record_card_payload(
    *,
    record_id: str,
    question: str | None,
    method: str,
    coins: list[list[str]],
    resolved: ResolvedHexagram,
    preprocess: dict[str, Any],
    interpretation: dict[str, Any],
    cast_trace: dict[str, Any] | None = None,
    created_at: str | None = None,
    random_mode: bool = False,
) -> dict[str, Any]:
    classic = classic_text_for(resolved)
    display_coins = _display_coin_faces(coins)
    display_interpretation = _normalize_interpretation(interpretation)
    primary_text = classic["primary"]
    changed_text = classic["changed"]
    rows = []
    for pos in range(6, 0, -1):
        value = resolved.line_values[pos - 1]
        primary_bit = resolved.primary_bits[pos - 1]
        changed_bit = resolved.changed_bits[pos - 1]
        yaoci = primary_text["yaoci"][pos - 1]
        label = line_label(pos, primary_bit)
        rows.append(
            {
                "position": pos,
                "label": label,
                "shape": render_line_shape(primary_bit, value in (6, 9)),
                "changed_shape": render_line_shape(changed_bit, False),
                "is_yang": bool(primary_bit),
                "value": value,
                "name": LINE_NAME[value],
                "change": LINE_CHANGE[value],
                "yaoci": _yaoci_body(yaoci, label),
                "is_moving": value in (6, 9),
            }
        )
    return {
        "title": "易经起卦记录" if not random_mode else "随机一卦",
        "record_id": record_id,
        "created_at": created_at or "",
        "question": question or "（未提供具体问题）",
        "method": METHOD_NAME.get(method, method),
        "method_raw": method,
        "coins": display_coins,
        "coin_rows": _coin_rows(display_coins),
        "cast_trace": cast_trace or {},
        "has_coins": bool(display_coins),
        "has_yarrow_trace": (cast_trace or {}).get("kind") == "manual_yarrow",
        "line_values": resolved.line_values,
        "moving_positions": resolved.moving_positions,
        "primary": resolved.primary,
        "changed": resolved.changed,
        "primary_text": primary_text,
        "changed_text": changed_text,
        "line_rows": rows,
        "preprocess": preprocess,
        "interpretation": display_interpretation,
        "sources": sources(),
    }


def build_record_payload_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_by_lines(data["line_values"])
    return build_record_card_payload(
        record_id=data["id"],
        question=data["question"],
        method=data["method"],
        coins=data.get("coins", []),
        resolved=resolved,
        preprocess=data.get("preprocess", {}),
        interpretation=data.get("interpretation", {}),
        cast_trace=data.get("cast_trace", {}),
        created_at=data.get("created_at", ""),
        random_mode=data.get("method") == "random",
    )


def build_history_payload(records: list[Any]) -> dict[str, Any]:
    items = []
    by_seq = hexagram_by_seq()
    for record in records:
        data = record_to_dict(record)
        p = by_seq[data["primary_seq"]]
        c = by_seq.get(data["changed_seq"]) if data.get("changed_seq") else None
        items.append(
            {
                "id": data["id"],
                "created_at": data["created_at"],
                "question": data["question"],
                "method": METHOD_NAME.get(data["method"], data["method"]),
                "primary": p,
                "changed": c,
                "moving_positions": data["moving_positions"],
            }
        )
    return {"title": "易经历史记录", "items": items}


def build_hexagram_query_payload(query: str, interpretation: dict[str, Any] | None = None) -> dict[str, Any]:
    hexagram = find_hexagram(query)
    if hexagram is None:
        return {"found": False, "query": query, "title": "解卦结果"}
    resolved = resolve_static_hexagram(int(hexagram["seq"]))
    interpretation = interpretation or {
        "summary": f"你查询的是 {hexagram['name']} 卦。当前为静卦查询，不针对具体问题推演。",
        "answer_to_question": f"你查询的是 {hexagram['name']} 卦。",
        "hexagram_structure": "静态卦象查询。",
        "current_situation": get_hexagram_text(int(hexagram["seq"]))["guaci"].get("text", ""),
        "changing_line_focus": "静态查卦无动爻。",
        "change_trend": "静态查卦不产生变卦。",
        "actionable_advice": ["可结合卦辞、大象和六爻位置理解该卦。"],
        "risks": [],
        "disclaimer": "本结果为传统文本解释，不构成现实决策建议。",
    }
    return build_record_card_payload(
        record_id="QUERY",
        question=f"查询：{query}",
        method="query",
        coins=[],
        resolved=resolved,
        preprocess={"allowed": True, "warnings": [], "llm_used": False},
        interpretation=interpretation,
        cast_trace={"kind": "query"},
    )
