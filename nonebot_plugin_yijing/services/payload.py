from __future__ import annotations

from typing import Any

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
    created_at: str | None = None,
    random_mode: bool = False,
) -> dict[str, Any]:
    classic = classic_text_for(resolved)
    primary_text = classic["primary"]
    changed_text = classic["changed"]
    rows = []
    for pos in range(6, 0, -1):
        value = resolved.line_values[pos - 1]
        primary_bit = resolved.primary_bits[pos - 1]
        changed_bit = resolved.changed_bits[pos - 1]
        yaoci = primary_text["yaoci"][pos - 1]
        rows.append(
            {
                "position": pos,
                "label": line_label(pos, primary_bit),
                "shape": render_line_shape(primary_bit, value in (6, 9)),
                "changed_shape": render_line_shape(changed_bit, False),
                "value": value,
                "name": LINE_NAME[value],
                "change": LINE_CHANGE[value],
                "yaoci": yaoci.get("text", "爻辞待补录。"),
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
        "coins": coins,
        "has_coins": bool(coins),
        "line_values": resolved.line_values,
        "moving_positions": resolved.moving_positions,
        "primary": resolved.primary,
        "changed": resolved.changed,
        "primary_text": primary_text,
        "changed_text": changed_text,
        "line_rows": rows,
        "preprocess": preprocess,
        "interpretation": interpretation,
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
        created_at=data.get("created_at", ""),
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


def build_hexagram_query_payload(query: str) -> dict[str, Any]:
    hexagram = find_hexagram(query)
    if hexagram is None:
        return {"found": False, "query": query, "title": "解卦结果"}
    resolved = resolve_static_hexagram(int(hexagram["seq"]))
    interpretation = {
        "summary": f"你查询的是 {hexagram['name']} 卦。当前为静卦查询，不针对具体问题推演。",
        "current_situation": get_hexagram_text(int(hexagram["seq"]))["guaci"].get("text", ""),
        "change_trend": "静态查卦不产生变卦。",
        "advice": ["可结合卦辞、大象和六爻位置理解该卦。"],
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
    )
