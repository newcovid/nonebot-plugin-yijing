from __future__ import annotations

from datetime import datetime

from nonebot_plugin_yijing.models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota
from nonebot_plugin_yijing.services.repository import record_to_dict


def test_model_table_names_use_plugin_prefix() -> None:
    assert CastRecord.__tablename__ == "nonebot_plugin_yijing_cast_record"
    assert GroupConfig.__tablename__ == "nonebot_plugin_yijing_group_config"
    assert RuntimeQuota.__tablename__ == "nonebot_plugin_yijing_runtime_quota"
    assert GroupCooldown.__tablename__ == "nonebot_plugin_yijing_group_cooldown"


def test_group_config_has_window_settings() -> None:
    columns = GroupConfig.__table__.columns

    assert "duplicate_window_minutes" in columns
    assert "history_minutes_for_llm" in columns
    assert columns["duplicate_window_minutes"].default is not None
    assert columns["history_minutes_for_llm"].default is not None


def test_cast_record_has_cast_trace_field() -> None:
    columns = CastRecord.__table__.columns

    assert "cast_trace_json" in columns
    assert columns["cast_trace_json"].default is not None


def test_cast_record_index_names_are_stable() -> None:
    index_names = {index.name for index in CastRecord.__table__.indexes}

    assert index_names == {
        "ix_yijing_cast_group",
        "ix_yijing_cast_user",
        "ix_yijing_cast_question",
        "ix_yijing_cast_time",
    }


def test_runtime_quota_index_names_are_stable() -> None:
    index_names = {index.name for index in RuntimeQuota.__table__.indexes}

    assert index_names == {
        "ix_yijing_quota_group",
        "ix_yijing_quota_user",
        "ix_yijing_quota_time",
    }


def test_record_to_dict_serializes_loaded_cast_record() -> None:
    record = CastRecord(
        id="YJ-TEST0002",
        adapter="onebot.v11",
        bot_id="10000",
        group_id="20000",
        user_id_hash="user-hash",
        question_text="项目推进是否顺利",
        question_norm="项目推进是否顺利",
        question_hash="question-hash",
        method="yarrow",
        coins_json="[]",
        line_values_json="[7, 7, 7, 7, 7, 7]",
        moving_positions_json="[]",
        cast_trace_json='{"kind": "yarrow"}',
        primary_seq=1,
        changed_seq=None,
        preprocess_json='{"allowed": true, "warnings": [], "llm_used": false}',
        interpretation_json='{"summary": "测试摘要", "advice": ["测试建议"]}',
        created_at=datetime(2026, 7, 8, 12, 30, 0),
    )

    data = record_to_dict(record)

    assert data["id"] == "YJ-TEST0002"
    assert data["question"] == "项目推进是否顺利"
    assert data["method"] == "yarrow"
    assert data["line_values"] == [7, 7, 7, 7, 7, 7]
    assert data["moving_positions"] == []
    assert data["primary_seq"] == 1
    assert data["changed_seq"] is None
    assert data["coins"] == []
    assert data["cast_trace"]["kind"] == "yarrow"
    assert data["preprocess"]["allowed"] is True
    assert data["interpretation"]["summary"] == "测试摘要"
    assert data["created_at"] == "2026-07-08 12:30:00"
