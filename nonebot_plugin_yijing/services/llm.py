from __future__ import annotations

import json
from typing import Any

import aiohttp
from nonebot.log import logger
from pydantic import ValidationError

from ..config import plugin_config
from ..core.hexagram import ResolvedHexagram
from ..core.interpret import build_local_interpretation, local_preprocess
from ..core.llm_models import (
    InterpretationLLMOutput,
    InterpretationResult,
    LLMStatus,
    PreprocessLLMOutput,
    PreprocessResult,
    model_dump,
    model_validate,
)


class LLMUnavailable(RuntimeError):
    pass


def _enabled() -> bool:
    return bool(
        plugin_config.yijing_llm_enabled
        and plugin_config.yijing_llm_base_url
        and plugin_config.yijing_llm_model
        and plugin_config.yijing_llm_api_key
    )


def llm_config_ready() -> bool:
    """Return whether the global provider configuration is complete."""

    return _enabled()


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
    if not isinstance(content, dict):
        raise TypeError("LLM response content must be an object")
    return content


def _fallback_preprocess(
    local: dict[str, Any], status: LLMStatus, reason: str
) -> dict[str, Any]:
    return model_dump(
        model_validate(
            PreprocessResult,
            {
                **local,
                "llm_used": False,
                "llm_status": status,
                "fallback_reason": reason,
            }
        )
    )


def _fallback_interpretation(
    fallback: dict[str, Any], status: LLMStatus, reason: str
) -> dict[str, Any]:
    return model_dump(
        model_validate(
            InterpretationResult,
            {
                **fallback,
                "llm_used": False,
                "llm_status": status,
                "fallback_reason": reason,
            }
        )
    )


def _is_invalid_response_error(exc: Exception) -> bool:
    return isinstance(exc, (ValidationError, json.JSONDecodeError, KeyError, TypeError, ValueError))


def _merge_unique(*groups: list[str]) -> list[str]:
    return list(dict.fromkeys(item for group in groups for item in group if item))


async def preprocess_question(
    question: str, history: list[dict[str, Any]], *, use_llm: bool = True
) -> dict[str, Any]:
    local = local_preprocess(question, history)
    if not local["allowed"] or not use_llm:
        return local
    if not _enabled():
        return _fallback_preprocess(local, "fallback_config", "incomplete_config")

    history_questions = []
    if not local["sensitive_keywords"]:
        history_questions = [
            str(item.get("question") or "").strip()
            for item in history
            if str(item.get("question") or "").strip()
        ]
    system = (
        "你是一个NoneBot易经插件的安全预处理器。必须只输出JSON。"
        "判断问题是否适合起卦，遵循不诚不占、不义不占、不疑不占；"
        "只能输出要求的字段，不要解卦，不要编造卦象。"
    )
    payload = {
        "question": question,
        "recent_questions": history_questions,
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
        raw = await _chat_json(system, payload)
        output = model_validate(PreprocessLLMOutput, raw)
        output_data = model_dump(output, exclude_none=True)
        merged = {
            **local,
            **output_data,
            "allowed": bool(local["allowed"] and output_data.get("allowed", True)),
            "warnings": _merge_unique(local["warnings"], output_data.get("warnings", [])),
            "sensitive_keywords": _merge_unique(
                local["sensitive_keywords"], output_data.get("sensitive_keywords", [])
            ),
            "history_count": len(history),
            "llm_used": True,
            "llm_status": "success",
            "fallback_reason": None,
        }
        return model_dump(model_validate(PreprocessResult, merged))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM preprocess failed: {exc}")
        if _is_invalid_response_error(exc):
            return _fallback_preprocess(local, "fallback_invalid", "invalid_response")
        return _fallback_preprocess(local, "fallback_request", "request_failed")


def _minimal_classic_context(
    resolved: ResolvedHexagram, classic_text: dict[str, Any]
) -> dict[str, Any]:
    primary = classic_text["primary"]
    changed = classic_text.get("changed")
    moving_lines = []
    for position in resolved.moving_positions:
        item = primary.get("yaoci", [])[position - 1]
        moving_lines.append(
            {
                "position": position,
                "label": item.get("line_label", ""),
                "text": item.get("text", ""),
            }
        )
    context: dict[str, Any] = {
        "primary": {
            "seq": resolved.primary["seq"],
            "name": resolved.primary["name"],
            "lower_trigram": resolved.primary.get("lower_trigram", ""),
            "upper_trigram": resolved.primary.get("upper_trigram", ""),
            "guaci": primary.get("guaci", {}).get("text", ""),
            "daxiang": primary.get("xiang", {}).get("daxiang", ""),
        },
        "line_values_bottom_up": resolved.line_values,
        "moving_lines": moving_lines,
    }
    if resolved.changed and changed:
        context["changed"] = {
            "seq": resolved.changed["seq"],
            "name": resolved.changed["name"],
            "lower_trigram": resolved.changed.get("lower_trigram", ""),
            "upper_trigram": resolved.changed.get("upper_trigram", ""),
            "guaci": changed.get("guaci", {}).get("text", ""),
            "daxiang": changed.get("xiang", {}).get("daxiang", ""),
        }
    return context


def _merge_interpretation(
    fallback: dict[str, Any], output: InterpretationLLMOutput
) -> dict[str, Any]:
    output_data = model_dump(output, exclude_none=True)
    merged = {
        **fallback,
        **output_data,
        "risks": _merge_unique(fallback["risks"], output_data.get("risks", [])),
        "disclaimer": fallback["disclaimer"],
        "llm_used": True,
        "llm_status": "success",
        "fallback_reason": None,
    }
    return model_dump(model_validate(InterpretationResult, merged))


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
    if random_mode or not use_llm:
        return fallback
    if not _enabled():
        return _fallback_interpretation(fallback, "fallback_config", "incomplete_config")
    system = (
        "你是《周易》文本解释助手。必须只输出JSON。"
        "基于用户问题和提供的最小经典上下文作现代解释；"
        "不得输出或改写经典原文字段，不得给出确定性预测，"
        "不得替代医疗、法律、财务或安全专业人士。"
    )
    payload = {
        "question": question,
        "hexagram_context": _minimal_classic_context(resolved, classic_text),
        "preprocess": {
            "warnings": preprocess.get("warnings", []),
            "sensitive_keywords": preprocess.get("sensitive_keywords", []),
        },
        "required_schema": {
            "summary": "str",
            "answer_to_question": "str",
            "hexagram_structure": "str",
            "current_situation": "str",
            "changing_line_focus": "str",
            "change_trend": "str",
            "actionable_advice": "list[str]",
            "risks": "list[str]",
            "disclaimer": "str",
        },
    }
    try:
        raw = await _chat_json(system, payload)
        return _merge_interpretation(fallback, model_validate(InterpretationLLMOutput, raw))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM interpretation failed: {exc}")
        if _is_invalid_response_error(exc):
            return _fallback_interpretation(fallback, "fallback_invalid", "invalid_response")
        return _fallback_interpretation(fallback, "fallback_request", "request_failed")


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


async def interpret_hexagram_query(
    *,
    query: str,
    resolved: ResolvedHexagram,
    classic_text: dict[str, Any],
    use_llm: bool = True,
) -> dict[str, Any]:
    fallback = build_local_interpretation(f"查询：{query}", resolved)
    fallback["answer_to_question"] = (
        f"你查询的是 {resolved.primary['name']} 卦；静态查卦不针对具体事件作预测。"
    )
    fallback["change_trend"] = "静态查卦不产生变卦。"
    fallback["actionable_advice"] = ["可结合卦辞、大象和六爻位置理解该卦。"]
    fallback = model_dump(model_validate(InterpretationResult, fallback))
    if not use_llm:
        return fallback
    if not _enabled():
        return _fallback_interpretation(fallback, "fallback_config", "incomplete_config")
    system = (
        "你是《周易》静态卦象解释助手。必须只输出JSON。"
        "只能基于查询词和提供的经典上下文解释，不得编造起卦过程或确定性预测。"
    )
    payload = {
        "query": query,
        "hexagram_context": _minimal_classic_context(resolved, classic_text),
        "required_schema": {
            "summary": "str",
            "answer_to_question": "str",
            "hexagram_structure": "str",
            "current_situation": "str",
            "changing_line_focus": "str",
            "change_trend": "str",
            "actionable_advice": "list[str]",
            "risks": "list[str]",
            "disclaimer": "str",
        },
    }
    try:
        raw = await _chat_json(system, payload)
        return _merge_interpretation(fallback, model_validate(InterpretationLLMOutput, raw))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Yijing LLM query interpretation failed: {exc}")
        if _is_invalid_response_error(exc):
            return _fallback_interpretation(fallback, "fallback_invalid", "invalid_response")
        return _fallback_interpretation(fallback, "fallback_request", "request_failed")
