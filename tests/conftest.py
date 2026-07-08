from __future__ import annotations

import nonebot


# Several modules import plugin_config at module import time. Initialize a minimal
# NoneBot driver before test modules import those modules.
nonebot.init(
    _env_file=None,
    sqlalchemy_database_url="sqlite+aiosqlite:///:memory:",
    yijing_user_hash_salt="test-salt",
    yijing_llm_enabled=False,
)
