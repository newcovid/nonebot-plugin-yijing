import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "nonebot_plugin_yijing" / "data"
SCRAPED_CLASSICAL_FILES = [
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
    "special_texts.json",
]
RESERVED_EXTENSION_FILES = [
    "dynasty_commentaries.json",
    "meihua_rules.json",
    "najia_rules.json",
    "ganzhi_calendar.json",
    "wuxing_strength.json",
    "liuqin_liushen.json",
    "modern_explanations.json",
    "scenario_templates.json",
]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_data_shape():
    assert len(load("trigrams.json")) == 8
    assert len(load("hexagrams.json")) == 64
    assert len(load("lines.json")) == 384
    assert len(load("guaci.json")) == 64
    assert len(load("yaoci.json")) == 384


def test_hexagram_bits_unique():
    hexagrams = load("hexagrams.json")
    assert len({h["binary_bottom_up"] for h in hexagrams}) == 64


def test_seeded_need():
    need = [x for x in load("yaoci.json") if x["hexagram_seq"] == 5]
    assert len(need) == 6
    assert need[0]["text"].startswith("初九：需于郊")
    assert need[-1]["text"].startswith("上六：入于穴")


def test_scraped_classical_layers_have_no_placeholders():
    for filename in SCRAPED_CLASSICAL_FILES:
        raw = (ROOT / filename).read_text(encoding="utf-8")

        assert "待补录" not in raw, filename
        assert '"status": "placeholder"' not in raw, filename


def test_scraped_records_are_source_located():
    source_ids = {item["id"] for item in load("sources.json")}

    for filename in ["guaci.json", "yaoci.json", "tuan.json"]:
        for item in load(filename):
            assert item["source_id"] in source_ids
            assert item["status"] == "checked"
            assert item.get("source_locator")

    for filename in [
        "wenyan.json",
        "xici_shang.json",
        "xici_xia.json",
        "shuogua.json",
        "xugua.json",
        "zagua.json",
        "special_texts.json",
    ]:
        for item in load(filename):
            assert item["source_id"] in source_ids
            assert item["status"] == "checked"
            assert item.get("source_locator")

    for item in load("xiang.json"):
        assert item["source_id"] in source_ids
        assert item["status"] == "checked"
        assert item.get("source_locator")
        assert item["daxiang_source_id"] in source_ids
        assert item["daxiang_status"] == "checked"
        assert item.get("daxiang_source_locator")
        assert len(item["xiaoxiang"]) == 6
        for xiaoxiang in item["xiaoxiang"]:
            assert xiaoxiang["source_id"] in source_ids
            assert xiaoxiang["status"] == "checked"
            assert xiaoxiang.get("source_locator")


def test_reserved_extension_layers_start_empty_and_schema_managed():
    manifest = load("schemas/manifest.json")

    for filename in RESERVED_EXTENSION_FILES:
        assert load(filename) == []
        assert manifest["files"][filename] == "reserved_extension.schema.json"


def test_qian_terms_are_normalized_without_rewriting_legal_gan_terms():
    xici_shang_raw = (ROOT / "xici_shang.json").read_text(encoding="utf-8")
    yaoci_raw = (ROOT / "yaoci.json").read_text(encoding="utf-8")
    wenyan_raw = (ROOT / "wenyan.json").read_text(encoding="utf-8")

    assert "乾之策" in xici_shang_raw
    assert "干之策" not in xici_shang_raw
    assert "干父之蛊" in yaoci_raw
    assert "事之干也" in wenyan_raw
