from __future__ import annotations

import json

from nonebot_plugin_yijing.core.data import (
    DATA_DIR,
    get_hexagram_text,
    schema_manifest,
    sources,
    special_texts,
    tuan,
    wenyan,
    xiang,
)

CORE_DATA_FILES = {
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
    "special_texts.json",
    "reserved_tables.json",
    "dynasty_commentaries.json",
    "meihua_rules.json",
    "najia_rules.json",
    "ganzhi_calendar.json",
    "wuxing_strength.json",
    "liuqin_liushen.json",
    "modern_explanations.json",
    "scenario_templates.json",
}


def test_schema_manifest_covers_all_core_data_files() -> None:
    manifest = schema_manifest()
    files = manifest["files"]

    assert set(files) == CORE_DATA_FILES
    for data_file, schema_file in files.items():
        assert (DATA_DIR / data_file).exists()
        schema_path = DATA_DIR / "schemas" / schema_file
        assert schema_path.exists(), f"missing schema for {data_file}: {schema_file}"
        json.loads(schema_path.read_text(encoding="utf-8"))


def test_runtime_hexagram_text_exposes_extended_corpus_layers() -> None:
    text = get_hexagram_text(1)

    assert text["guaci"]
    assert text["yaoci"]
    assert text["tuan"]
    assert text["xiang"]
    assert "wenyan" in text
    assert "special_texts" in text
    assert {item["label"] for item in text["special_texts"]} == {"用九"}


def test_wenyan_is_scoped_to_canonical_qian_kun_only() -> None:
    records = wenyan()

    assert set(records) == {1, 2}
    assert all(item["scope"] == "canonical_wenyan" for item in records.values())


def test_xiang_xiaoxiang_uses_structured_line_records() -> None:
    for item in xiang().values():
        assert isinstance(item["xiaoxiang"], list)
        assert "xiaoxiang_by_position" in item
        for xiao in item["xiaoxiang"]:
            assert isinstance(xiao, dict)
            assert {"position", "line_label", "text", "source_id", "status"} <= set(xiao)


def test_special_texts_are_outside_ordinary_six_line_slots() -> None:
    records = special_texts()
    labels = {(item["hexagram_seq"], item["label"]) for item in records}

    assert labels == {(1, "用九"), (2, "用六")}
    assert all(item["kind"] == "special_line_text" for item in records)


def test_classical_text_sources_are_registered() -> None:
    source_ids = {item["id"] for item in sources()}

    for item in tuan().values():
        assert item["source_id"] in source_ids
    for item in wenyan().values():
        assert item["source_id"] in source_ids
    for item in special_texts():
        assert item["source_id"] in source_ids
    for item in xiang().values():
        assert item["source_id"] in source_ids
        for xiao in item["xiaoxiang"]:
            assert xiao["source_id"] in source_ids
