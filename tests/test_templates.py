from __future__ import annotations

import importlib.resources as resources


def test_cast_card_keeps_six_line_heading_clean_and_uses_geometric_lines() -> None:
    template = (
        resources.files("nonebot_plugin_yijing") / "templates" / "card.html"
    ).read_text(encoding="utf-8")

    assert "<h2>六爻结果</h2>" in template
    assert "六爻结果（上爻在上，初爻在下）" not in template
    assert 'class="line-symbol"' in template
    assert 'class="line-segment"' in template
