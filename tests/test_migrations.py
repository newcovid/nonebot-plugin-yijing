from __future__ import annotations

import importlib.resources as resources

from nonebot_plugin_yijing.models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota


MIGRATION_FILE = "20260708_01_initial_yijing_tables.py"


def _migration_text() -> str:
    migrations = resources.files("nonebot_plugin_yijing") / "migrations"
    return (migrations / MIGRATION_FILE).read_text(encoding="utf-8")


def test_initial_migration_is_packaged() -> None:
    migrations = resources.files("nonebot_plugin_yijing") / "migrations"

    assert (migrations / "__init__.py").is_file()
    assert (migrations / MIGRATION_FILE).is_file()


def test_initial_migration_uses_plugin_branch_label() -> None:
    text = _migration_text()

    assert 'revision: str = "20260708_01"' in text
    assert 'down_revision: str | Sequence[str] | None = None' in text
    assert 'branch_labels: str | Sequence[str] | None = ("nonebot_plugin_yijing",)' in text


def test_initial_migration_mentions_all_model_tables() -> None:
    text = _migration_text()

    for model in (CastRecord, GroupConfig, GroupCooldown, RuntimeQuota):
        assert model.__tablename__ in text


def test_initial_migration_mentions_model_indexes() -> None:
    text = _migration_text()
    expected_index_names = {
        "ix_yijing_cast_group",
        "ix_yijing_cast_user",
        "ix_yijing_cast_question",
        "ix_yijing_cast_time",
        "ix_yijing_quota_group",
        "ix_yijing_quota_user",
        "ix_yijing_quota_time",
    }

    for index_name in expected_index_names:
        assert index_name in text
