from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nonebot_plugin_yijing import __plugin_meta__
from nonebot_plugin_yijing.render import message as message_module


@pytest.mark.asyncio
async def test_image_message_uses_current_adapter_export(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    expected = object()

    async def fake_export(message: Any) -> object:
        captured["message"] = message
        return expected

    monkeypatch.setattr(message_module.UniMessage, "export", fake_export)

    assert await message_module.image_message(b"image-bytes") is expected
    assert captured["message"][0].raw == b"image-bytes"


def test_package_declares_all_adapters_without_onebot_dependency() -> None:
    pyproject = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(
        encoding="utf-8"
    )

    assert __plugin_meta__.supported_adapters is None
    assert "nonebot-adapter-onebot" not in pyproject
