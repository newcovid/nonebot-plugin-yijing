from __future__ import annotations

import json
from typing import Any

import aiohttp
from nonebot.log import logger

from ..config import plugin_config
from ..core.interpret import build_local_interpretation, local_preprocess
from ..core.hexagram import ResolvedHexagram


class LLMUnavailable(RuntimeError):
    pass


def _enabled() -> bool:
    return bool(
        plugin_config.yijing_llm_enabled
        and plugin_config.yijing_llm_base_url
        and plugin_config.yijing_llm_model
        and plugin_config.yijing_llm_api_key
    )


async def _chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    if not _enabled():
        raise LLMUnavailable("LLM disabled or incomplete config")
    base = plugin_config.yijing_llm_base_url.rstrip("/")
    api_key = plugin_config.yijing_llm_api_key.get_secret_value() if plugin_config.yijing_llm_api_key else ""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": plugin_config.yijing_llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    timeout = aiohttp.ClientTimeout(total=plugin_config.yijing_llm_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        async with client.post(f"{base}/chat/completions", headers=headers, json=body) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise LLMUnavailable(f"LLM HTTP {resp.status}: {text[:200]}")
            data = json.loads(text)
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return json.loads(content)
    return content


async def preprocess_question(question: str, history: list[dict[str, Any]], *, use_llm: bool = True) -> dict[str, Any]:
    local = local_preprocess(question, history)
    if not use_llm or not _enabled():
        return local
    system = (
        "你是一个NoneBot易经插件的安全预处理器。必须只输出JSON。"
        "任务：判断用户问题是否适合起卦；遵循三不占：不诚不占、不义不占、不疑不占；"
        "识别短期相似问题、敏感领域、是否需要提示专业建议。"
        "不要进行正式解卦，不要编造卦象。"
    )
    payload = {
        "question": question,
        "history": history,
        "required_schema": {
            "allowed": "bool",
            "reason": "str",
            "warnings": "list[str]",
            "sensitive_keywords": "list[str]",
            "similar_record_id": "str|null",
            "suggest_reuse_history": "bool",
        },
    }
    try:
        result = await _chat_json(system, payload)
        merged = {**local, **result, "llm_used": True, "history_count": len(history)}
        if "warnings" not in merged or not isinstance(merged["warnings"], list):
            merged["warnings"] = local.get("warnings", [])
        return merged
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM preprocess failed: {exc}")
        return local


async def interpret_with_llm(
    *,
    question: str | None,
    resolved: ResolvedHexagram,
    classic_text: dict[str, Any],
    preprocess: dict[str, Any],
    random_mode: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    fallback = build_local_interpretation(question, resolved, preprocess, random_mode=random_mode)
    if random_mode or not use_llm or not _enabled():
        return fallback
    system = (
        "你是一个《周易》文本解释助手。必须只输出JSON。"
        "只能基于用户问题、卦象、卦辞、象辞、爻辞进行解释；"
        "必须区分经典文本与现代建议；不得给出确定性预测；"
        "不得代替医生、律师、财务顾问或安全专业人士。"
    )
    payload = {
        "question": question,
        "primary_hexagram": resolved.primary,
        "changed_hexagram": resolved.changed,
        "line_values_bottom_up": resolved.line_values,
        "moving_positions": resolved.moving_positions,
        "classic_text": classic_text,
        "preprocess": preprocess,
        "required_schema": {
            "summary": "str",
            "current_situation": "str",
            "change_trend": "str",
            "advice": "list[str]",
            "risks": "list[str]",
            "disclaimer": "str",
        },
    }
    try:
        result = await _chat_json(system, payload)
        result["llm_used"] = True
        return {**fallback, **result}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM interpretation failed: {exc}")
        return fallback


async def parse_hexagram_query(query: str) -> dict[str, Any]:
    if not _enabled():
        return {"query": query, "llm_used": False}
    system = "你是《周易》卦名解析器。只输出JSON，字段 normalized_query。"
    try:
        result = await _chat_json(system, {"query": query})
        result["llm_used"] = True
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM parse hexagram failed: {exc}")
        return {"query": query, "llm_used": False}
