from __future__ import annotations

from nonebot.adapters import Message
from nonebot_plugin_alconna import Image, UniMessage


async def image_message(image: bytes) -> Message:
    """将图片导出为当前适配器的消息。"""
    return await UniMessage(Image(raw=image)).export()
