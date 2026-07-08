from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from nonebot import get_driver
from nonebot.adapters import Event

from .config import plugin_config


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_group_id(event: Event) -> str:
    group_id = getattr(event, "group_id", None)
    if group_id is not None:
        return str(group_id)
    guild_id = getattr(event, "guild_id", None)
    channel_id = getattr(event, "channel_id", None)
    if guild_id is not None and channel_id is not None:
        return f"guild:{guild_id}:{channel_id}"
    return "private"


def get_user_id(event: Event) -> str:
    user_id = getattr(event, "user_id", None)
    if user_id is not None:
        return str(user_id)
    return str(event.get_user_id())


def hash_user_id(user_id: str) -> str:
    salt = plugin_config.yijing_user_hash_salt
    return hashlib.sha256(f"{salt}:{user_id}".encode("utf-8")).hexdigest()


def normalize_question(text: str | None) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"[\s\u3000]+", "", text)
    text = re.sub(r"[，。！？；：、,.!?;:'\"“”‘’【】\[\]()（）<>《》]+", "", text)
    return text


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # 适合中文短句的轻量 n-gram Jaccard。
    def grams(s: str) -> set[str]:
        if len(s) <= 2:
            return {s}
        return {s[i : i + 2] for i in range(len(s) - 1)}

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def parse_command_body(raw: str, command: str) -> str:
    raw = raw.strip()
    for prefix in ("/", "！", "!", ""):
        head = f"{prefix}{command}"
        if raw.startswith(head):
            return raw[len(head) :].strip()
    return raw


def event_is_group_admin(event: Event) -> bool:
    sender = getattr(event, "sender", None)
    role = getattr(sender, "role", "") if sender else ""
    if role in {"admin", "owner"}:
        return True
    try:
        return get_user_id(event) in get_driver().config.superusers
    except Exception:
        return False


def compact_dict(value: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: value.get(k) for k in keys if k in value}


def get_plain_text(event: Event) -> str:
    if hasattr(event, "get_plaintext"):
        try:
            return str(event.get_plaintext())
        except Exception:
            pass
    try:
        return str(event.get_message())
    except Exception:
        return str(event)
