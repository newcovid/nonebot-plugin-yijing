from __future__ import annotations

import os

import nonebot
import pytest


TEST_ASYNC_DATABASE_URL = os.getenv("YIJING_TEST_DATABASE_URL")
TEST_SYNC_DATABASE_URL = os.getenv("YIJING_TEST_SYNC_DATABASE_URL")


# Several modules import plugin_config at module import time. Initialize a minimal
# NoneBot driver before test modules import those modules.
nonebot.init(
    _env_file=None,
    sqlalchemy_database_url=(
        TEST_ASYNC_DATABASE_URL
        or "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/yijing_test"
    ),
    yijing_user_hash_salt="test-salt",
    yijing_llm_enabled=False,
)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    if TEST_ASYNC_DATABASE_URL is None:
        pytest.skip("YIJING_TEST_DATABASE_URL is required for database integration tests")
    return TEST_ASYNC_DATABASE_URL


@pytest.fixture(scope="session")
def test_sync_database_url() -> str:
    if TEST_SYNC_DATABASE_URL is None:
        pytest.skip("YIJING_TEST_SYNC_DATABASE_URL is required for migration integration tests")
    return TEST_SYNC_DATABASE_URL
