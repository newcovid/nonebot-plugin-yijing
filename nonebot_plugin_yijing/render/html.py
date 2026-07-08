from __future__ import annotations

from pathlib import Path
from typing import Any

from nonebot import require

require("nonebot_plugin_htmlrender")

from nonebot_plugin_htmlrender import render_template

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


async def render_image(template_name: str, data: dict[str, Any]) -> bytes:
    """用 nonebot-plugin-htmlrender 渲染模板为图片。

    0.7.1 里 render_template 不传 pages.base_url 时会默认使用 file://{Path.cwd()}。
    在本容器里 cwd=/app，Chromium 会先打开目录页，触发 start/addRow 等目录页脚本警告。
    本插件模板目前全部内联 CSS，不依赖相对静态资源，因此直接使用 about:blank。
    """
    return await render_template(
        str(TEMPLATE_DIR),
        template_name=template_name,
        templates=data,
        pages={
            "viewport": {"width": 920, "height": 10},
            "base_url": "about:blank",
        },
        wait=50,
        device_scale_factor=2,
        screenshot_timeout=60_000,
    )
