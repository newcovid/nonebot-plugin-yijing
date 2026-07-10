from __future__ import annotations

from typing import Any

import pytest

from nonebot_plugin_yijing.core.hexagram import resolve_by_lines
from nonebot_plugin_yijing.core.interpret import build_local_interpretation, local_preprocess
from nonebot_plugin_yijing.services import llm as llm_service
from nonebot_plugin_yijing.services.payload import classic_text_for


def test_local_preprocess_schema_is_stable_for_normal_question() -> None:
    result = local_preprocess("此行去山西实习一程怎么样", [])

    assert set(result) >= {
        "allowed",
        "reason",
        "warnings",
        "sensitive_keywords",
        "llm_used",
        "history_count",
    }
    assert result["allowed"] is True
    assert result["llm_used"] is False
    assert result["history_count"] == 0


def test_local_preprocess_rejects_empty_question() -> None:
    result = local_preprocess("", [])

    assert result["allowed"] is False
    assert "不疑不占" in result["reason"]


def test_local_preprocess_adds_sensitive_warning() -> None:
    result = local_preprocess("投资股票是否应该加仓", [])

    assert result["allowed"] is True
    assert result["sensitive_keywords"]
    assert any("专业人士" in warning for warning in result["warnings"])


def test_local_interpretation_schema_is_stable() -> None:
    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])
    preprocess = local_preprocess("项目推进是否顺利", [])
    result = build_local_interpretation("项目推进是否顺利", resolved, preprocess)

    assert set(result) >= {
        "schema_version",
        "summary",
        "answer_to_question",
        "hexagram_structure",
        "current_situation",
        "changing_line_focus",
        "change_trend",
        "actionable_advice",
        "risks",
        "relations",
        "llm_used",
        "disclaimer",
    }
    assert result["llm_used"] is False
    assert isinstance(result["actionable_advice"], list)
    assert result["disclaimer"]


@pytest.mark.asyncio
async def test_preprocess_llm_malformed_json_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _broken_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        raise ValueError(f"malformed json: {system}:{user_payload}")

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _broken_chat_json)

    result = await llm_service.preprocess_question("项目推进是否顺利", [], use_llm=True)

    assert result["allowed"] is True
    assert result["llm_used"] is False
    assert result["history_count"] == 0
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio
async def test_preprocess_llm_missing_fields_keep_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _partial_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        return {"reason": f"LLM 已处理：{bool(system and user_payload)}"}

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _partial_chat_json)

    history = [{"id": "YJ-OLD0001", "question": "项目推进是否顺利"}]
    result = await llm_service.preprocess_question("项目推进是否顺利", history, use_llm=True)

    assert result["allowed"] is True
    assert result["llm_used"] is True
    assert result["history_count"] == 1
    assert result["sensitive_keywords"] == []
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio
async def test_interpret_llm_malformed_json_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _broken_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        raise ValueError(f"malformed json: {system}:{user_payload}")

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _broken_chat_json)

    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])
    preprocess = local_preprocess("项目推进是否顺利", [])
    fallback = build_local_interpretation("项目推进是否顺利", resolved, preprocess)
    result = await llm_service.interpret_with_llm(
        question="项目推进是否顺利",
        resolved=resolved,
        classic_text=classic_text_for(resolved),
        preprocess=preprocess,
        use_llm=True,
    )

    assert result["summary"] == fallback["summary"]
    assert result["actionable_advice"] == fallback["actionable_advice"]
    assert result["llm_status"] == "fallback_invalid"
    assert result["fallback_reason"] == "invalid_response"


@pytest.mark.asyncio
async def test_interpret_llm_missing_fields_keep_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _partial_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        return {"summary": f"LLM 摘要：{bool(system and user_payload)}"}

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _partial_chat_json)

    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])
    preprocess = local_preprocess("项目推进是否顺利", [])
    result = await llm_service.interpret_with_llm(
        question="项目推进是否顺利",
        resolved=resolved,
        classic_text=classic_text_for(resolved),
        preprocess=preprocess,
        use_llm=True,
    )

    assert result["llm_used"] is True
    assert result["summary"] == "LLM 摘要：True"
    assert result["current_situation"]
    assert isinstance(result["actionable_advice"], list)
    assert result["disclaimer"]


@pytest.mark.asyncio
async def test_local_refusal_never_calls_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def _unexpected_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal called
        called = bool(system and user_payload)
        return {}

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _unexpected_chat_json)

    result = await llm_service.preprocess_question("我想作弊害人", [], use_llm=True)

    assert result["allowed"] is False
    assert result["llm_status"] == "not_requested"
    assert called is False


@pytest.mark.asyncio
async def test_sensitive_preprocess_omits_history(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _capture_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        captured.update(user_payload)
        return {"allowed": True}

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _capture_chat_json)

    result = await llm_service.preprocess_question(
        "投资股票是否应该加仓",
        [{"id": "YJ-SECRET", "question": "此前的敏感问题", "user_id": "secret"}],
        use_llm=True,
    )

    assert result["llm_status"] == "success"
    assert captured["recent_questions"] == []
    assert "YJ-SECRET" not in str(captured)
    assert "user_id" not in str(captured)


@pytest.mark.asyncio
async def test_interpretation_rejects_extra_classical_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _extra_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "摘要", "classic_text": "被改写的经典"}

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _extra_chat_json)
    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])

    result = await llm_service.interpret_with_llm(
        question="项目推进是否顺利",
        resolved=resolved,
        classic_text=classic_text_for(resolved),
        preprocess=local_preprocess("项目推进是否顺利", []),
        use_llm=True,
    )

    assert result["llm_used"] is False
    assert result["llm_status"] == "fallback_invalid"


@pytest.mark.asyncio
async def test_cast_pipeline_makes_preprocess_then_interpretation_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def _ordered_chat_json(system: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(user_payload)
        if "recent_questions" in user_payload:
            return {"allowed": True, "warnings": []}
        return {
            "summary": "综合摘要",
            "answer_to_question": "可以推进，但应分阶段验证。",
            "hexagram_structure": "乾下乾上。",
            "current_situation": "当前具备推进条件。",
            "changing_line_focus": "无动爻，重在守正。",
            "change_trend": "保持稳定。",
            "actionable_advice": ["先完成小范围验证。"],
            "risks": [],
            "disclaimer": "仅供参考。",
        }

    monkeypatch.setattr(llm_service, "_enabled", lambda: True)
    monkeypatch.setattr(llm_service, "_chat_json", _ordered_chat_json)
    question = "项目推进是否顺利"
    preprocess = await llm_service.preprocess_question(question, [], use_llm=True)
    resolved = resolve_by_lines([7, 7, 7, 7, 7, 7])
    interpretation = await llm_service.interpret_with_llm(
        question=question,
        resolved=resolved,
        classic_text=classic_text_for(resolved),
        preprocess=preprocess,
        use_llm=True,
    )

    assert len(calls) == 2
    assert "recent_questions" in calls[0]
    assert "hexagram_context" in calls[1]
    assert "primary_hexagram" not in calls[1]
    assert interpretation["llm_status"] == "success"
    assert interpretation["answer_to_question"] == "可以推进，但应分阶段验证。"
