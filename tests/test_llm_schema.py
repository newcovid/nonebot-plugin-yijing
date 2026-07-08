from __future__ import annotations

from nonebot_plugin_yijing.core.interpret import build_local_interpretation, local_preprocess
from nonebot_plugin_yijing.core.hexagram import resolve_by_lines


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
