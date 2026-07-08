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
        "summary",
        "current_situation",
        "change_trend",
        "advice",
        "risks",
        "relations",
        "llm_used",
        "disclaimer",
    }
    assert result["llm_used"] is False
    assert isinstance(result["advice"], list)
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

    assert result == fallback


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
    assert isinstance(result["advice"], list)
    assert result["disclaimer"]
