from __future__ import annotations

import importlib.resources as resources

from jinja2 import Environment, FileSystemLoader, select_autoescape

from nonebot_plugin_yijing.commands.main import HELP_COMMANDS
from nonebot_plugin_yijing.core.hexagram import resolve_by_lines
from nonebot_plugin_yijing.services.payload import build_record_card_payload


def _environment() -> Environment:
    templates = resources.files("nonebot_plugin_yijing") / "templates"
    with resources.as_file(templates) as path:
        return Environment(
            loader=FileSystemLoader(str(path)),
            autoescape=select_autoescape(["html"]),
        )


def test_cast_card_keeps_six_line_heading_clean_and_uses_geometric_lines() -> None:
    template = (
        resources.files("nonebot_plugin_yijing") / "templates" / "card.html"
    ).read_text(encoding="utf-8")

    assert "<h2>六爻结果</h2>" in template
    assert "六爻结果（上爻在上，初爻在下）" not in template
    assert 'class="line-symbol"' in template
    assert 'class="line-segment"' in template
    assert "radial-gradient" not in template
    assert 'class="coin-dot"' in template


def test_help_template_renders_nested_subcommands() -> None:
    template = (
        resources.files("nonebot_plugin_yijing") / "templates" / "help.html"
    ).read_text(encoding="utf-8")

    assert "{% if item.children %}" in template
    assert "{% for child in item.children %}" in template


def test_all_cards_extend_the_shared_visual_base() -> None:
    templates = resources.files("nonebot_plugin_yijing") / "templates"

    for filename in ("card.html", "help.html", "history.html", "notice.html", "settings.html"):
        text = (templates / filename).read_text(encoding="utf-8")
        assert '{% extends "base.html" %}' in text


def test_five_card_fixtures_render_with_shared_theme() -> None:
    environment = _environment()
    resolved = resolve_by_lines([7, 8, 9, 6, 7, 8])
    card = build_record_card_payload(
        record_id="YJ-VISUAL01",
        question="这是一个用于验证长文本换行和视觉层级的示例问题" * 4,
        method="coin",
        coins=[["正", "反", "正"]] * 6,
        resolved=resolved,
        preprocess={"allowed": True, "warnings": [], "llm_used": False},
        interpretation={"summary": "摘要", "advice": ["旧格式建议"]},
        cast_trace={"kind": "coin"},
    )
    fixtures = {
        "card.html": card,
        "help.html": {"commands": HELP_COMMANDS},
        "history.html": {"title": "易经历史记录", "items": []},
        "notice.html": {"title": "提示", "content": "内容" * 100, "hint": "操作提示"},
        "settings.html": {"rows": [{"name": "本群LLM解读", "value": "开启"}]},
    }

    for template_name, payload in fixtures.items():
        rendered = environment.get_template(template_name).render(**payload)
        assert "--paper: #fffaf0" in rendered
        assert "class=\"page\"" in rendered

    rendered_card = environment.get_template("card.html").render(**card)
    assert 'coin positive' in rendered_card
    assert 'coin negative' in rendered_card
    assert '<span class="coin-dot"></span>' not in rendered_card
    assert "本地规则解读" in rendered_card

    fallback_card = build_record_card_payload(
        record_id="YJ-FALLBACK",
        question="铜钱面文缺失兜底",
        method="coin",
        coins=[["", "", ""]],
        resolved=resolved,
        preprocess={"allowed": True, "warnings": [], "llm_used": False},
        interpretation={"summary": "摘要", "advice": []},
        cast_trace={"kind": "coin"},
    )
    rendered_fallback = environment.get_template("card.html").render(**fallback_card)
    assert rendered_fallback.count('<span class="coin-dot"></span>') == 3
