from __future__ import annotations

from nonebot import require
from nonebot.plugin import PluginMetadata

from .config import YijingConfig

require("nonebot_plugin_alconna")
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_orm")
require("nonebot_plugin_localstore")

# 权限控制插件是强依赖；API 适配用于将本插件拆成细粒度服务。
require("nonebot_plugin_access_control")
require("nonebot_plugin_access_control_api")

__plugin_meta__ = PluginMetadata(
    name="易经起卦解卦",
    description="群内自助进行基于《周易》的起卦、查卦、解卦、历史记录与图片化输出。",
    usage="""
易经帮助
起卦 <问题>
起卦 <问题> 铜钱
起卦 <问题> 大衍
起卦 <问题> 手动
解卦 <卦名/卦象>
易经历史
易经记录 <ID>
易经清理 <ID|全部>
随机一卦
易经设置
""".strip(),
    type="application",
    homepage="https://github.com/newcovid/nonebot-plugin-yijing",
    config=YijingConfig,
)

from . import commands as _commands  # noqa: E402,F401
