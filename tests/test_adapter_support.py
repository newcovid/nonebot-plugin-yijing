from __future__ import annotations

import ast
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


def test_package_declares_all_adapters_without_forcing_platform_dependencies() -> None:
    project_root = Path(__file__).resolve().parent.parent
    plugin_init = (project_root / "nonebot_plugin_yijing" / "__init__.py").read_text(
        encoding="utf-8"
    )
    pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")

    assert __plugin_meta__.supported_adapters is None
    assert "supported_adapters=None" in plugin_init
    assert "nonebot-adapter-" not in pyproject
    assert '"nonebot-plugin-orm>=0.7.0"' in pyproject


def test_source_imports_only_nonebot_adapter_abstractions() -> None:
    package_root = Path(__file__).resolve().parent.parent / "nonebot_plugin_yijing"
    allowed_abstractions = {"Bot", "Event", "Message"}
    concrete_imports: list[str] = []

    for path in package_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("nonebot.adapters."):
                    concrete_imports.append(f"{path}:{node.lineno}:{node.module}")
                elif node.module == "nonebot.adapters":
                    unexpected = {alias.name for alias in node.names} - allowed_abstractions
                    concrete_imports.extend(
                        f"{path}:{node.lineno}:nonebot.adapters.{name}"
                        for name in sorted(unexpected)
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("nonebot.adapters."):
                        concrete_imports.append(f"{path}:{node.lineno}:{alias.name}")

    assert concrete_imports == []
