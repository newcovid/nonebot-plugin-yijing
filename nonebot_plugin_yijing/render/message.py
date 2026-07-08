from __future__ import annotations

from nonebot.adapters import Message


def image_message(image: bytes) -> Message:
    """构造图片消息。当前发布版优先支持 OneBot V11。"""
    try:
        from nonebot.adapters.onebot.v11 import MessageSegment

        return MessageSegment.image(image)
    except Exception:  # noqa: BLE001
        try:
            from nonebot_plugin_alconna import UniMessage, Image

            return UniMessage(Image(raw=image)).export()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("当前适配器暂不支持原始图片 bytes 发送。") from exc
