import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "nonebot_plugin_yijing" / "data"


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
