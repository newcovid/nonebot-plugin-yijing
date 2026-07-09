from __future__ import annotations

from importlib import util as importlib_util
import importlib.resources as resources
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from nonebot_plugin_yijing.models import CastRecord, GroupConfig, GroupCooldown, RuntimeQuota


INITIAL_MIGRATION_FILE = "20260708_01_initial_yijing_tables.py"
WINDOWS_MIGRATION_FILE = "20260708_02_add_group_setting_windows.py"
LEGACY_MIGRATION_FILE = "8f2b7c4a1d00_init_yijing.py"


def _migration_text(filename: str) -> str:
    migrations = resources.files("nonebot_plugin_yijing") / "migrations"
    return (migrations / filename).read_text(encoding="utf-8")


def test_migrations_are_packaged() -> None:
    migrations = resources.files("nonebot_plugin_yijing") / "migrations"

    assert (migrations / "__init__.py").is_file()
    assert (migrations / INITIAL_MIGRATION_FILE).is_file()
    assert (migrations / WINDOWS_MIGRATION_FILE).is_file()
    assert not (migrations / LEGACY_MIGRATION_FILE).is_file()


def test_initial_migration_uses_plugin_branch_label() -> None:
    text = _migration_text(INITIAL_MIGRATION_FILE)

    assert 'revision: str = "20260708_01"' in text
    assert 'down_revision: str | Sequence[str] | None = None' in text
    assert 'branch_labels: str | Sequence[str] | None = ("nonebot_plugin_yijing",)' in text


def test_alembic_revision_graph_has_single_yijing_head() -> None:
    orm_spec = importlib_util.find_spec("nonebot_plugin_orm")
    assert orm_spec is not None
    assert orm_spec.submodule_search_locations is not None

    migrations = resources.files("nonebot_plugin_yijing") / "migrations"
    with resources.as_file(migrations) as migrations_path:
        config = Config()
        config.set_main_option(
            "script_location",
            str(Path(orm_spec.submodule_search_locations[0]) / "templates" / "generic"),
        )
        config.set_main_option("version_locations", str(migrations_path))
        config.set_main_option("path_separator", "os")

        script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20260708_02"]
    assert script.get_revision("nonebot_plugin_yijing").revision == "20260708_01"
    assert script.get_revision("20260708_02").down_revision == "20260708_01"


def test_initial_migration_mentions_all_model_tables() -> None:
    text = _migration_text(INITIAL_MIGRATION_FILE)

    for model in (CastRecord, GroupConfig, GroupCooldown, RuntimeQuota):
        assert model.__tablename__ in text


def test_initial_migration_mentions_model_indexes() -> None:
    text = _migration_text(INITIAL_MIGRATION_FILE)
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


def test_windows_migration_extends_initial_migration() -> None:
    text = _migration_text(WINDOWS_MIGRATION_FILE)

    assert 'revision: str = "20260708_02"' in text
    assert 'down_revision: str | Sequence[str] | None = "20260708_01"' in text
    assert '"duplicate_window_minutes"' in text
    assert '"history_minutes_for_llm"' in text
    assert 'server_default="30"' in text
    assert 'server_default="120"' in text
