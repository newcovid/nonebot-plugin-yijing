from __future__ import annotations

import importlib.resources as resources

from nonebot_plugin_yijing.core.data import load_json


REQUIRED_JSON_FILES = [
    "trigrams.json",
    "hexagrams.json",
    "lines.json",
    "guaci.json",
    "yaoci.json",
    "tuan.json",
    "xiang.json",
    "wenyan.json",
    "xici_shang.json",
    "xici_xia.json",
    "shuogua.json",
    "xugua.json",
    "zagua.json",
    "relations.json",
    "sources.json",
    "casting_rules.json",
    "interpret_rules.json",
    "reserved_tables.json",
    "dynasty_commentaries.json",
    "meihua_rules.json",
    "najia_rules.json",
    "ganzhi_calendar.json",
    "wuxing_strength.json",
    "liuqin_liushen.json",
    "modern_explanations.json",
    "scenario_templates.json",
]
RESERVED_EXTENSION_FILES = {
    "dynasty_commentaries.json",
    "meihua_rules.json",
    "najia_rules.json",
    "ganzhi_calendar.json",
    "wuxing_strength.json",
    "liuqin_liushen.json",
    "modern_explanations.json",
    "scenario_templates.json",
}


def test_required_json_files_exist_in_package_resources() -> None:
    data_root = resources.files("nonebot_plugin_yijing") / "data"

    for filename in REQUIRED_JSON_FILES:
        assert (data_root / filename).is_file(), filename


def test_required_json_files_are_loadable() -> None:
    for filename in REQUIRED_JSON_FILES:
        payload = load_json(filename)
        assert payload is not None, filename
        if filename not in RESERVED_EXTENSION_FILES:
            assert len(payload) > 0, filename
