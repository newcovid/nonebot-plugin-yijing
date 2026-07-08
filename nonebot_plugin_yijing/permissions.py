from __future__ import annotations

from nonebot import require

require("nonebot_plugin_access_control_api")

from nonebot_plugin_access_control_api.service import create_plugin_service

plugin_service = create_plugin_service("nonebot_plugin_yijing")

cast_service = plugin_service.create_subservice("cast")
query_service = plugin_service.create_subservice("query")
history_service = plugin_service.create_subservice("history")
settings_service = plugin_service.create_subservice("settings")
random_service = plugin_service.create_subservice("random")
manual_service = plugin_service.create_subservice("manual")
