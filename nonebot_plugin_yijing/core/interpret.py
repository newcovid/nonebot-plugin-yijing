from __future__ import annotations

from typing import Any

from .data import get_hexagram_text, relations
from .hexagram import ResolvedHexagram

SENSITIVE_KEYWORDS = {
    "疾病", "病", "癌", "手术", "吃药", "药", "法律", "官司", "诉讼", "判刑", "投资", "股票", "基金",
    "币", "贷款", "借钱", "自杀", "轻生", "伤害", "杀", "危险", "事故", "人身安全", "怀孕", "抑郁",
}


def detect_sensitive(question: str | None) -> list[str]:
    if not question:
        return []
    hits = [kw for kw in SENSITIVE_KEYWORDS if kw in question]
    return sorted(set(hits), key=len, reverse=True)


def local_preprocess(question: str | None, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    q = (question or "").strip()
    warnings: list[str] = []
    allowed = True
    reason = ""
    if not q:
        allowed = False
        reason = "不疑不占：未提供明确问题。"
    elif any(x in q for x in ["害人", "报复", "作弊", "诈骗", "违法"]):
        allowed = False
        reason = "不义不占：问题可能涉及不义或违法目的。"
    elif len(q) < 4:
        warnings.append("问题较短，建议补充背景后再占。")
    sensitive = detect_sensitive(q)
    if sensitive:
        warnings.append("问题涉及敏感领域，结果仅供传统文化文本解释；请咨询专业人士。")
    return {
        "allowed": allowed,
        "reason": reason,
        "warnings": warnings,
        "sensitive_keywords": sensitive,
        "llm_used": False,
        "history_count": len(history or []),
    }


def build_local_interpretation(
    question: str | None,
    resolved: ResolvedHexagram,
    preprocess: dict[str, Any] | None = None,
    random_mode: bool = False,
) -> dict[str, Any]:
    primary_text = get_hexagram_text(int(resolved.primary["seq"]))
    moving = resolved.moving_positions
    p_name = resolved.primary["name"]
    c_name = resolved.changed["name"] if resolved.changed else "无变卦"
    if random_mode:
        summary = f"本次随机得到 {p_name} 卦。它可作为今日观察主题，而不是针对具体问题的预测。"
    elif moving:
        summary = f"所问之事以 {p_name} 为当前格局，动爻在 {','.join(map(str, moving))} 爻，变化趋势指向 {c_name}。"
    else:
        summary = f"所问之事以 {p_name} 为主，无动爻，宜重点参考本卦卦辞与大象。"
    advice = []
    if moving:
        advice.append("先看本卦所示处境，再看动爻提示的关键节点，最后看变卦所示趋势。")
    else:
        advice.append("无动爻时不宜过度推演变化，重点放在当下格局与守正。")
    advice.append("涉及重大现实决策时，请把卦象作为反思工具，而不是唯一依据。")
    risks = []
    if preprocess and preprocess.get("sensitive_keywords"):
        risks.append("涉及疾病、法律、投资、人身安全等问题时，请咨询专业人士。")
    rels = [r for r in relations() if r["hexagram_seq"] == int(resolved.primary["seq"])]
    return {
        "summary": summary,
        "current_situation": f"{p_name}：{primary_text['guaci']['text']}",
        "change_trend": f"变卦：{c_name}" if resolved.changed else "无变卦：局势重在守持当前原则。",
        "advice": advice,
        "risks": risks,
        "relations": rels[:3],
        "llm_used": False,
        "disclaimer": "本结果为《周易》文本与传统文化规则的娱乐性解释，不构成医疗、法律、投资或安全建议。",
    }
