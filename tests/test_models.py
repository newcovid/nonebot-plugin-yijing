from __future__ import annotations

from nonebot_plugin_yijing.models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota


def test_model_table_names_use_plugin_prefix() -> None:
    assert CastRecord.__tablename__ == "nonebot_plugin_yijing_cast_record"
    assert GroupConfig.__tablename__ == "nonebot_plugin_yijing_group_config"
    assert RuntimeQuota.__tablename__ == "nonebot_plugin_yijing_runtime_quota"
    assert GroupCooldown.__tablename__ == "nonebot_plugin_yijing_group_cooldown"


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
