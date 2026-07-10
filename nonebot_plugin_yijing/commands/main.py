from __future__ import annotations

import time
from typing import Any

from arclet.alconna import Alconna, AllParam, Args
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.rule import Rule
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_orm import async_scoped_session

from ..config import plugin_config
from ..core.caster import (
    cast_coin,
    cast_random_hexagram,
    cast_yarrow,
)
from ..core.hexagram import resolve_by_lines
from ..core.interpret import local_preprocess
from ..core.manual import advance_manual_coin, advance_manual_yarrow, parse_yarrow_split
from ..permissions import (
    cast_service,
    history_service,
    manual_service,
    query_service,
    random_service,
    settings_service,
)
from ..render.html import render_image
from ..render.message import image_message
from ..services.llm import (
    interpret_hexagram_query,
    interpret_with_llm,
    llm_config_ready,
    parse_hexagram_query,
    preprocess_question,
)
from ..services.payload import (
    build_hexagram_query_payload,
    build_history_payload,
    build_record_card_payload,
    build_record_payload_from_dict,
    classic_text_for,
)
from ..services.repository import (
    add_quota,
    all_user_records,
    cooldown_remaining,
    daily_quota_count,
    delete_user_records,
    find_similar_recent,
    get_or_create_group_config,
    get_record_for_view,
    recent_records,
    record_to_dict,
    save_record,
    touch_cooldown,
)
from ..utils import (
    event_is_group_admin,
    get_group_id,
    get_plain_text,
    get_user_id,
    hash_user_id,
    normalize_question,
    parse_command_body,
    utcnow,
)


def _all_args_command(name: str) -> Alconna:
    return Alconna(name, Args["body?", AllParam])


help_matcher = on_alconna(Alconna("易经帮助"), aliases={"周易帮助"})
cast_matcher = on_alconna(_all_args_command("起卦"), aliases={"算卦"})
query_matcher = on_alconna(_all_args_command("解卦"))
history_matcher = on_alconna(Alconna("易经历史"))
record_matcher = on_alconna(_all_args_command("易经记录"))
history_cleanup_matcher = on_alconna(_all_args_command("易经清理"))
random_matcher = on_alconna(Alconna("随机一卦"))
settings_matcher = on_alconna(_all_args_command("易经设置"))

for matcher, service in [
    (cast_matcher, cast_service),
    (query_matcher, query_service),
    (history_matcher, history_service),
    (record_matcher, history_service),
    (history_cleanup_matcher, history_service),
    (random_matcher, random_service),
    (settings_matcher, settings_service),
    (help_matcher, query_service),
]:
    service.patch_matcher(matcher)


async def _finish_template(matcher: Matcher, template: str, data: dict[str, Any]) -> None:
    image = await render_image(template, data)
    await matcher.finish(await image_message(image))


async def _notice(matcher: Matcher, title: str, content: str, hint: str = "") -> None:
    await _finish_template(matcher, "notice.html", {"title": title, "content": content, "hint": hint})


def _parse_cast_body(body: str) -> tuple[str, str, bool]:
    parts = body.strip().split()
    force = "--force" in parts
    body = " ".join(part for part in parts if part != "--force")
    method = "default"
    suffix_map = [
        ("大衍", "yarrow"),
        ("蓍草", "yarrow"),
        ("铜钱", "coin"),
        ("硬币", "coin"),
        ("手动", "manual"),
    ]
    for suffix, value in suffix_map:
        if body.endswith(suffix):
            method = value
            body = body[: -len(suffix)].strip()
            break
    if not body and method != "manual":
        return "", method, force
    return body, method, force


def _manual_key(bot: Bot, event: Event) -> tuple[str, str, str, str]:
    return (
        str(getattr(bot, "type", "")),
        str(getattr(bot, "self_id", "")),
        get_group_id(event),
        get_user_id(event),
    )


def _manual_expired(state: dict[str, Any]) -> bool:
    started_at = float(state.get("updated_at", state.get("started_at", 0)))
    return time.time() - started_at > plugin_config.yijing_manual_session_timeout_seconds


def _touch_manual(state: dict[str, Any]) -> None:
    state["updated_at"] = time.time()


_parse_yarrow_split = parse_yarrow_split


def _yarrow_prompt(state: dict[str, Any]) -> tuple[str, str]:
    line = int(state["line"])
    change = int(state["change"])
    total = int(state["current_total"])
    return (
        f"大衍第 {line} 爻第 {change} 变",
        f"请将 {total} 根蓍草任意分成左右两堆，并输入左右数量。\n"
        "输入格式：左 右，例如：24 25。\n发送“取消”可退出本次手动起卦。",
    )


def _manual_coin_trace(values: list[int], coins: list[list[str]]) -> dict[str, Any]:
    return {
        "kind": "manual_coin",
        "lines_bottom_up": [
            {"position": index + 1, "faces": faces, "value": values[index]}
            for index, faces in enumerate(coins)
        ],
    }


def _parse_positive_int(text: str, *, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError("数值必须是整数。") from exc
    if value < minimum:
        raise ValueError(f"数值不能小于 {minimum}。")
    if maximum is not None and value > maximum:
        raise ValueError(f"数值不能大于 {maximum}。")
    return value


def _parse_history_cleanup_target(body: str) -> str | None:
    target = body.strip()
    if target in {"全部", "全量"} or target.lower() == "all":
        return None
    record_id = target.upper()
    if (
        record_id.startswith("YJ-")
        and 3 < len(record_id) <= 32
        and record_id[3:].isalnum()
    ):
        return record_id
    raise ValueError("请使用：易经清理 YJ-XXXXXXXX；全量清理请使用：易经清理 全部")


def _set_group_llm_enabled(cfg: Any, enabling: bool) -> bool:
    """Set the group switch and return whether the one-time privacy notice is due."""

    cfg.llm_enabled = enabling
    if enabling and not cfg.llm_privacy_notice_shown:
        cfg.llm_privacy_notice_shown = True
        return True
    return False


def _history_brief(records: list[Any]) -> list[dict[str, Any]]:
    items = []
    for r in records:
        data = record_to_dict(r)
        items.append(
            {
                "id": data["id"],
                "created_at": data["created_at"],
                "question": data["question"],
                "primary_seq": data["primary_seq"],
                "changed_seq": data["changed_seq"],
                "moving_positions": data["moving_positions"],
            }
        )
    return items


async def _run_cast(
    *,
    matcher: Matcher,
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    question: str | None,
    method: str,
    manual_values: list[int] | None = None,
    manual_coins: list[list[str]] | None = None,
    manual_trace: dict[str, Any] | None = None,
    random_mode: bool = False,
    force_recast: bool = False,
) -> None:
    group_id = get_group_id(event)
    user_hash = hash_user_id(get_user_id(event))
    cfg = await get_or_create_group_config(session, group_id)
    if not cfg.enabled and not event_is_group_admin(event):
        await _notice(matcher, "易经插件已关闭", "本群已关闭易经插件。")
    if method == "default":
        method = cfg.default_method

    if question and not random_mode and not force_recast:
        similar = await find_similar_recent(
            session,
            group_id=group_id,
            user_hash=user_hash,
            question=question,
            minutes=cfg.duplicate_window_minutes,
        )
        if similar:
            record, _score = similar
            await _finish_template(
                matcher,
                "card.html",
                build_record_payload_from_dict(record_to_dict(record)),
            )
            return

    if random_mode:
        preprocess = {
            "allowed": True,
            "reason": "",
            "warnings": [],
            "sensitive_keywords": [],
            "llm_used": False,
            "history_count": 0,
            "random_mode": True,
        }
    elif question:
        history = await recent_records(
            session,
            group_id=group_id,
            user_hash=user_hash,
            limit=20,
            minutes=cfg.history_minutes_for_llm,
        )
        preprocess = await preprocess_question(question, _history_brief(history), use_llm=cfg.llm_enabled)
        if not preprocess.get("allowed", True):
            await _notice(
                matcher,
                "本次未起卦",
                str(preprocess.get("reason") or "根据三不占预处理规则，本次不建议起卦。"),
                "你可以重新整理成一个明确、正当且确有疑问的问题。",
            )
    else:
        preprocess = local_preprocess(question or "", [])

    if not random_mode:
        quota = await daily_quota_count(session, group_id, user_hash)
        if quota >= cfg.daily_limit:
            await _notice(
                matcher,
                "今日次数已达上限",
                f"你在本群 24 小时内已起卦 {quota} 次，上限为 {cfg.daily_limit} 次。",
            )

        remain = await cooldown_remaining(session, group_id, cfg.cooldown_seconds)
        if remain > 0:
            await _notice(matcher, "群冷却中", f"本群起卦冷却还剩 {remain} 秒。")

    if manual_values is not None:
        values = manual_values
        coins = manual_coins or []
        cast_method = method
        cast_trace = manual_trace or {"kind": method, "lines_bottom_up": [{"value": v} for v in values]}
    else:
        if random_mode:
            cast = cast_random_hexagram()
            values = cast.line_values
            coins = cast.coins
            cast_method = "random"
            cast_trace = {
                **(cast.trace or {}),
                "kind": "random",
                "selected_method": cast.method,
            }
        elif method == "yarrow":
            cast = cast_yarrow()
            values = cast.line_values
            coins = cast.coins
            cast_method = "yarrow"
            cast_trace = cast.trace or {}
        else:
            cast = cast_coin()
            values = cast.line_values
            coins = cast.coins
            cast_method = "coin"
            cast_trace = cast.trace or {}

    resolved = resolve_by_lines(values)
    classic = classic_text_for(resolved)
    interpretation = await interpret_with_llm(
        question=question,
        resolved=resolved,
        classic_text=classic,
        preprocess=preprocess,
        random_mode=random_mode,
        use_llm=cfg.llm_enabled,
    )
    adapter = getattr(bot, "type", "")
    bot_id = getattr(bot, "self_id", "")
    record = await save_record(
        session,
        adapter=str(adapter),
        bot_id=str(bot_id),
        group_id=group_id,
        user_hash=user_hash,
        question=question,
        method=cast_method,
        coins=coins,
        line_values=values,
        moving_positions=resolved.moving_positions,
        cast_trace=cast_trace,
        primary_seq=int(resolved.primary["seq"]),
        changed_seq=int(resolved.changed["seq"]) if resolved.changed else None,
        preprocess=preprocess,
        interpretation=interpretation,
    )
    record_id = record.id
    created_at = record.created_at.strftime("%Y-%m-%d %H:%M:%S")

    if not random_mode:
        await add_quota(session, group_id, user_hash)
        await touch_cooldown(
            session,
            group_id=group_id,
            record_id=record_id,
            user_hash=user_hash,
            question_norm=normalize_question(question),
        )
    payload = build_record_card_payload(
        record_id=record_id,
        question=question,
        method=cast_method,
        coins=coins,
        resolved=resolved,
        preprocess=preprocess,
        interpretation=interpretation,
        cast_trace=cast_trace,
        created_at=created_at,
        random_mode=random_mode,
    )
    await _finish_template(matcher, "card.html", payload)


HELP_COMMANDS = [
    {"cmd": "易经帮助", "desc": "查看所有交互命令。"},
    {"cmd": "起卦 问题 [--force]", "desc": "默认起卦；--force 仅用于跳过重复问题复用。"},
    {"cmd": "起卦 问题 铜钱", "desc": "精确指定三枚铜钱法。"},
    {"cmd": "起卦 问题 大衍", "desc": "使用大衍筮法概率模拟。"},
    {"cmd": "起卦 问题 手动", "desc": "进入手动引导：铜钱逐爻录入，大衍按十八变录入左右分堆。"},
    {"cmd": "解卦 卦象", "desc": "查询并解释卦名、卦序、符号或模糊卦象；启用 LLM 时会先归一化。"},
    {"cmd": "易经历史", "desc": "查看自己的最近起卦记录。"},
    {"cmd": "易经记录 ID", "desc": "查看指定记录的完整长图。"},
    {"cmd": "易经清理 ID / 全部", "desc": "清理指定记录，或清理本群全部个人历史。"},
    {"cmd": "随机一卦", "desc": "随机生成观察主题；保存历史但不占日限额、不触发群冷却。"},
    {
        "cmd": "易经设置",
        "desc": "查看或修改本群配置。以下子命令仅限群主、管理员或 superuser。",
        "children": [
            {"cmd": "开启 / 关闭", "desc": "启用或停用本群插件。"},
            {"cmd": "冷却 秒数", "desc": "设置群级起卦冷却，0 表示关闭冷却。"},
            {"cmd": "日限额 次数", "desc": "设置单用户 24 小时起卦次数上限。"},
            {"cmd": "重复窗口 分钟", "desc": "设置短期相似问题检测窗口。"},
            {"cmd": "历史窗口 分钟", "desc": "设置传给 LLM 预处理的近期历史窗口。"},
            {"cmd": "默认 铜钱 / 大衍", "desc": "设置本群默认起卦方式。"},
            {"cmd": "LLM 开启 / 关闭", "desc": "启用或停用本群 LLM 解读。"},
        ],
    },
]


@help_matcher.handle()
async def _help(matcher: Matcher) -> None:
    await _finish_template(matcher, "help.html", {"commands": HELP_COMMANDS})


@cast_matcher.handle()
async def _cast(bot: Bot, event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    raw = get_plain_text(event)
    body = parse_command_body(raw, "起卦")
    if raw.strip().startswith("算卦") or raw.strip().startswith("/算卦"):
        body = parse_command_body(raw, "算卦")
    question, method, force = _parse_cast_body(body)
    if method == "manual":
        if not question:
            await _notice(matcher, "缺少问题", "请使用：起卦 你的问题 手动")
        key = _manual_key(bot, event)
        existing = _MANUAL_SESSIONS.get(key)
        if existing and not _manual_expired(existing):
            await _notice(matcher, "已有手动起卦", "你当前已有未完成的手动起卦。发送“取消”可退出。")
        cfg = await get_or_create_group_config(session, get_group_id(event))
        if not force:
            similar = await find_similar_recent(
                session,
                group_id=get_group_id(event),
                user_hash=hash_user_id(get_user_id(event)),
                question=question,
                minutes=cfg.duplicate_window_minutes,
            )
            if similar:
                record, _score = similar
                await _finish_template(
                    matcher,
                    "card.html",
                    build_record_payload_from_dict(record_to_dict(record)),
                )
                return
        _MANUAL_SESSIONS[key] = {
            "question": question,
            "force_recast": True,
            "stage": "method",
            "started_at": time.time(),
            "updated_at": time.time(),
        }
        await _notice(
            matcher,
            "手动起卦引导",
            "请选择手动方式：\n1. 发送：铜钱\n2. 发送：大衍\n\n"
            "铜钱法随后逐爻输入每次投掷的 3 个正/反。\n"
            "大衍法随后按十八变输入每变左右两堆数量。",
        )
    if not question:
        await _notice(matcher, "缺少问题", "请使用：起卦 你的问题\n例如：起卦 此行去山西实习一程怎么样")
    await _run_cast(
        matcher=matcher,
        bot=bot,
        event=event,
        session=session,
        question=question,
        method=method,
        force_recast=force,
    )


@query_matcher.handle()
async def _query(event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    raw = get_plain_text(event)
    query = parse_command_body(raw, "解卦")
    if not query:
        await _notice(matcher, "缺少卦象", "请使用：解卦 需\n也可以输入卦序、卦名或符号。")
    cfg = await get_or_create_group_config(session, get_group_id(event))
    parsed = await parse_hexagram_query(query) if cfg.llm_enabled else {"query": query, "llm_used": False}
    q = str(parsed.get("normalized_query") or parsed.get("query") or query)
    payload = build_hexagram_query_payload(q)
    if not payload.get("found", True):
        await _notice(matcher, "未找到卦象", f"未能识别：{query}\n请尝试输入卦名，如：乾、坤、需；或输入 1-64。")
    resolved = resolve_by_lines(payload["line_values"])
    interpretation = await interpret_hexagram_query(
        query=q,
        resolved=resolved,
        classic_text=classic_text_for(resolved),
        use_llm=cfg.llm_enabled,
    )
    payload = build_hexagram_query_payload(q, interpretation=interpretation)
    await _finish_template(matcher, "card.html", payload)


@history_matcher.handle()
async def _history(event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    records = await all_user_records(
        session, group_id=get_group_id(event), user_hash=hash_user_id(get_user_id(event)), limit=20
    )
    await _finish_template(matcher, "history.html", build_history_payload(records))


@record_matcher.handle()
async def _record(event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    record_id = parse_command_body(get_plain_text(event), "易经记录").strip().upper()
    if not record_id:
        await _notice(matcher, "缺少记录 ID", "请使用：易经记录 YJ-XXXXXXXX")
    record = await get_record_for_view(
        session,
        record_id,
        group_id=get_group_id(event),
        user_hash=hash_user_id(get_user_id(event)),
        allow_group_admin=event_is_group_admin(event),
    )
    if record is None:
        await _notice(matcher, "记录不存在", f"未找到可查看的记录：{record_id}")
    await _finish_template(matcher, "card.html", build_record_payload_from_dict(record_to_dict(record)))


@history_cleanup_matcher.handle()
async def _history_cleanup(
    event: Event, matcher: Matcher, session: async_scoped_session
) -> None:
    body = parse_command_body(get_plain_text(event), "易经清理")
    try:
        record_id = _parse_history_cleanup_target(body)
    except ValueError as exc:
        await _notice(matcher, "清理格式错误", str(exc))
        return

    count = await delete_user_records(
        session,
        group_id=get_group_id(event),
        user_hash=hash_user_id(get_user_id(event)),
        record_id=record_id,
    )
    if record_id is not None and count == 0:
        await _notice(matcher, "记录不存在", f"未找到属于你的记录：{record_id}")
        return
    if record_id is None:
        content = f"已清理你在本群的 {count} 条起卦历史。"
    else:
        content = f"已清理起卦记录：{record_id}"
    await _notice(
        matcher,
        "历史已清理",
        content,
        "日限额和群冷却不受影响。",
    )


@random_matcher.handle()
async def _random(bot: Bot, event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    await _run_cast(
        matcher=matcher,
        bot=bot,
        event=event,
        session=session,
        question=None,
        method="random",
        random_mode=True,
    )


@settings_matcher.handle()
async def _settings(event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    group_id = get_group_id(event)
    cfg = await get_or_create_group_config(session, group_id)
    body = parse_command_body(get_plain_text(event), "易经设置").strip()
    changed = False
    show_llm_privacy_notice = False
    if body:
        if not event_is_group_admin(event):
            await _notice(matcher, "无权限", "设置类命令仅允许群主、管理员或 superuser 使用。")
        parts = body.split()
        try:
            if body in {"开启", "启用", "on"}:
                cfg.enabled = True
                changed = True
            elif body in {"关闭", "禁用", "off"}:
                cfg.enabled = False
                changed = True
            elif len(parts) >= 2 and parts[0] == "冷却":
                cfg.cooldown_seconds = _parse_positive_int(parts[1], minimum=0, maximum=86400)
                changed = True
            elif len(parts) >= 2 and parts[0] == "日限额":
                cfg.daily_limit = _parse_positive_int(parts[1], minimum=1, maximum=1000)
                changed = True
            elif len(parts) >= 2 and parts[0] == "重复窗口":
                cfg.duplicate_window_minutes = _parse_positive_int(parts[1], minimum=1, maximum=10080)
                changed = True
            elif len(parts) >= 2 and parts[0] == "历史窗口":
                cfg.history_minutes_for_llm = _parse_positive_int(parts[1], minimum=1, maximum=43200)
                changed = True
            elif len(parts) >= 2 and parts[0] == "默认":
                cfg.default_method = "yarrow" if parts[1] in {"大衍", "蓍草", "yarrow"} else "coin"
                changed = True
            elif len(parts) >= 2 and parts[0].upper() == "LLM":
                enabling = parts[1] in {"开启", "启用", "on", "true", "1"}
                show_llm_privacy_notice = _set_group_llm_enabled(cfg, enabling)
                changed = True
            else:
                await _notice(
                    matcher,
                    "设置格式错误",
                    "支持：易经设置 开启｜关闭｜冷却 秒数｜日限额 次数｜重复窗口 分钟｜历史窗口 分钟｜默认 铜钱/大衍｜LLM 开启/关闭",
                )
        except ValueError as exc:
            await _notice(matcher, "设置数值错误", str(exc), "请使用整数，例如：易经设置 重复窗口 30")
    if changed:
        cfg.updated_at = utcnow()
        await session.commit()
        await session.refresh(cfg)
    if show_llm_privacy_notice:
        readiness = "配置完整，可调用模型" if llm_config_ready() else "全局配置尚不完整，将使用本地降级"
        await _notice(
            matcher,
            "LLM 已开启 · 隐私提示",
            "本群问题可能会发送给管理员配置的第三方模型服务商。\n"
            "发送内容限于当前问题、必要卦象与经典文本；普通问题可能附带近期问题文本，"
            "敏感问题不会附带历史问题。\n"
            "不会发送群ID、用户ID、机器人ID或历史记录ID。",
            f"当前状态：{readiness}。关闭请使用：易经设置 LLM 关闭",
        )
    rows = [
        {"name": "群ID", "value": group_id},
        {"name": "是否启用", "value": "是" if cfg.enabled else "否"},
        {"name": "默认起卦方式", "value": "大衍" if cfg.default_method == "yarrow" else "铜钱"},
        {"name": "群冷却秒数", "value": cfg.cooldown_seconds},
        {"name": "用户24小时限额", "value": cfg.daily_limit},
        {"name": "重复问题窗口", "value": f"{cfg.duplicate_window_minutes} 分钟"},
        {"name": "LLM历史窗口", "value": f"{cfg.history_minutes_for_llm} 分钟"},
        {"name": "本群LLM解读", "value": "开启" if cfg.llm_enabled else "关闭"},
        {"name": "全局LLM开关", "value": "开启" if plugin_config.yijing_llm_enabled else "关闭"},
        {"name": "全局LLM就绪", "value": "是" if llm_config_ready() else "否（配置不完整）"},
        {"name": "随机一卦策略", "value": "保存历史，不占日限额，不触发冷却"},
        {"name": "手动会话超时", "value": f"{plugin_config.yijing_manual_session_timeout_seconds} 秒"},
        {"name": "铜钱输入", "value": f"{plugin_config.yijing_positive_face}/{plugin_config.yijing_negative_face}"},
    ]
    await _finish_template(matcher, "settings.html", {"rows": rows})


_MANUAL_SESSIONS: dict[tuple[str, str, str, str], dict[str, Any]] = {}


async def _has_manual_session(event: Event) -> bool:
    return any(key[2] == get_group_id(event) and key[3] == get_user_id(event) for key in _MANUAL_SESSIONS)


manual_input_matcher = on_message(rule=Rule(_has_manual_session), block=True, priority=5)
manual_service.patch_matcher(manual_input_matcher)


@manual_input_matcher.handle()
async def _manual_input(bot: Bot, event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    key = _manual_key(bot, event)
    state = _MANUAL_SESSIONS.get(key)
    if not state:
        return
    if _manual_expired(state):
        _MANUAL_SESSIONS.pop(key, None)
        await _notice(matcher, "手动起卦已超时", "请重新发送：起卦 你的问题 手动")
    text = get_plain_text(event).strip()
    if text in {"取消", "退出", "停止"}:
        _MANUAL_SESSIONS.pop(key, None)
        await _notice(matcher, "已取消", "本次手动起卦已取消。")
    _touch_manual(state)
    if state.get("stage") == "method":
        if text in {"铜钱", "硬币", "coin"}:
            state["stage"] = "coin_line"
            state["method"] = "manual_coin"
            state["line"] = 1
            state["coins"] = []
            state["values"] = []
            await _notice(
                matcher,
                "手动铜钱第 1 爻",
                f"请投掷三枚铜钱，输入第 1 爻的 3 个"
                f"{plugin_config.yijing_positive_face}/{plugin_config.yijing_negative_face}。\n"
                f"示例：{plugin_config.yijing_positive_face}{plugin_config.yijing_negative_face}"
                f"{plugin_config.yijing_positive_face}\n六爻均按自下而上录入。",
            )
        elif text in {"大衍", "蓍草", "yarrow"}:
            state["stage"] = "yarrow_change"
            state["method"] = "manual_yarrow"
            state["line"] = 1
            state["change"] = 1
            state["current_total"] = 49
            state["values"] = []
            state["yarrow_lines"] = []
            title, content = _yarrow_prompt(state)
            await _notice(matcher, title, "请准备 50 根蓍草或等量替代物，取 1 根不用，余 49 根开始。\n" + content)
        else:
            await _notice(matcher, "未识别方式", "请发送：铜钱 或 大衍。发送“取消”可退出。")

    if state.get("stage") == "coin_line":
        try:
            step = advance_manual_coin(state, text)
        except Exception as exc:  # noqa: BLE001
            await _notice(
                matcher,
                "输入格式错误",
                str(exc),
                f"请重试当前爻，例如：{plugin_config.yijing_positive_face}"
                f"{plugin_config.yijing_negative_face}{plugin_config.yijing_positive_face}。"
                "发送“取消”可退出。",
            )
            return
        state.clear()
        state.update(step.state)
        line = int(step.accepted["position"])
        value = int(step.accepted["value"])
        faces = list(step.accepted["faces"])
        if not step.completed:
            await _notice(
                matcher,
                f"手动铜钱第 {line + 1} 爻",
                f"已记录第 {line} 爻：{''.join(faces)} → {value}（进度 {line}/6）。\n"
                f"请继续输入第 {line + 1} 爻的 3 个"
                f"{plugin_config.yijing_positive_face}/{plugin_config.yijing_negative_face}。",
            )
            return
        values = list(state["values"])
        coins = list(state["coins"])
        _MANUAL_SESSIONS.pop(key, None)
        await _run_cast(
            matcher=matcher,
            bot=bot,
            event=event,
            session=session,
            question=state.get("question") or None,
            method="manual_coin",
            manual_values=values,
            manual_coins=coins,
            manual_trace=_manual_coin_trace(values, coins),
            force_recast=bool(state.get("force_recast")),
        )

    if state.get("stage") == "yarrow_change":
        try:
            step = advance_manual_yarrow(state, text)
        except Exception as exc:  # noqa: BLE001
            _title, retry_content = _yarrow_prompt(state)
            await _notice(matcher, "输入格式错误", str(exc), retry_content)
            return

        state.clear()
        state.update(step.state)
        removed = int(step.accepted["removed"])
        total_after = int(step.accepted["total_after"])
        if not step.line_completed:
            title, content = _yarrow_prompt(state)
            await _notice(
                matcher,
                title,
                f"上一变去除 {removed} 根，余 {total_after} 根。\n{content}",
            )
            return

        value = int(step.accepted["value"])
        line = int(step.accepted["position"])
        if not step.completed:
            title, content = _yarrow_prompt(state)
            await _notice(
                matcher,
                f"第 {line} 爻完成",
                f"第 {line} 爻三变后余 {total_after} 根，得爻值 {value}（进度 {line}/6）。\n"
                f"现在开始第 {line + 1} 爻。\n{content}",
            )
            return

        values = list(state["values"])
        trace = {"kind": "manual_yarrow", "lines_bottom_up": list(state["yarrow_lines"])}
        _MANUAL_SESSIONS.pop(key, None)
        await _run_cast(
            matcher=matcher,
            bot=bot,
            event=event,
            session=session,
            question=state.get("question") or None,
            method="manual_yarrow",
            manual_values=values,
            manual_coins=[],
            manual_trace=trace,
            force_recast=bool(state.get("force_recast")),
        )
