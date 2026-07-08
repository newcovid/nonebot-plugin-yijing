from __future__ import annotations

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
    parse_manual_coin,
    parse_manual_yarrow,
)
from ..core.hexagram import resolve_by_lines
from ..core.interpret import local_preprocess
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
from ..services.llm import interpret_with_llm, parse_hexagram_query, preprocess_question
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
    find_similar_recent,
    get_or_create_group_config,
    get_record,
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
random_matcher = on_alconna(Alconna("随机一卦"))
settings_matcher = on_alconna(_all_args_command("易经设置"))

for matcher, service in [
    (cast_matcher, cast_service),
    (query_matcher, query_service),
    (history_matcher, history_service),
    (record_matcher, history_service),
    (random_matcher, random_service),
    (settings_matcher, settings_service),
    (help_matcher, query_service),
]:
    service.patch_matcher(matcher)


async def _finish_template(matcher: Matcher, template: str, data: dict[str, Any]) -> None:
    image = await render_image(template, data)
    await matcher.finish(image_message(image))


async def _notice(matcher: Matcher, title: str, content: str, hint: str = "") -> None:
    await _finish_template(matcher, "notice.html", {"title": title, "content": content, "hint": hint})


def _parse_cast_body(body: str) -> tuple[str, str]:
    body = body.strip()
    method = "coin"
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
        return "", method
    return body, method


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
    random_mode: bool = False,
) -> None:
    group_id = get_group_id(event)
    user_hash = hash_user_id(get_user_id(event))
    cfg = await get_or_create_group_config(session, group_id)
    if not cfg.enabled and not event_is_group_admin(event):
        await _notice(matcher, "易经插件已关闭", "本群已关闭易经插件。")

    if not random_mode and question:
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
        similar = await find_similar_recent(
            session,
            group_id=group_id,
            user_hash=user_hash,
            question=question,
            minutes=cfg.duplicate_window_minutes,
        )
        if similar:
            record, score = similar
            await _notice(
                matcher,
                "发现短期相似问题",
                f"{cfg.duplicate_window_minutes} 分钟内你已问过相近问题。\n"
                f"记录ID：{record.id}\n相似度：{score:.2f}\n建议使用：易经记录 {record.id}",
                "如确实要重新起卦，可稍后再问，或由管理员调整冷却/重复窗口策略。",
            )
    else:
        preprocess = local_preprocess(question or "", [])

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
    else:
        if random_mode:
            cast = cast_random_hexagram()
            values = cast.line_values
            coins = cast.coins
            cast_method = "random"
        elif method == "yarrow":
            cast = cast_yarrow()
            values = cast.line_values
            coins = cast.coins
            cast_method = "yarrow"
        else:
            cast = cast_coin()
            values = cast.line_values
            coins = cast.coins
            cast_method = "coin"

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
        primary_seq=int(resolved.primary["seq"]),
        changed_seq=int(resolved.changed["seq"]) if resolved.changed else None,
        preprocess=preprocess,
        interpretation=interpretation,
    )
    record_id = record.id
    created_at = record.created_at.strftime("%Y-%m-%d %H:%M:%S")

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
        created_at=created_at,
        random_mode=random_mode,
    )
    await _finish_template(matcher, "card.html", payload)


@help_matcher.handle()
async def _help(matcher: Matcher) -> None:
    commands = [
        {"cmd": "易经帮助", "desc": "查看所有交互命令。"},
        {"cmd": "起卦 问题", "desc": "默认使用三枚铜钱法自动起卦并输出长图。"},
        {"cmd": "起卦 问题 铜钱", "desc": "精确指定三枚铜钱法。"},
        {"cmd": "起卦 问题 大衍", "desc": "使用大衍筮法概率模拟。"},
        {"cmd": "起卦 问题 手动", "desc": "进入手动引导，可输入铜钱正反或 6/7/8/9 爻值。"},
        {"cmd": "解卦 卦象", "desc": "查询并解释一个卦名、卦序、符号或模糊卦象。"},
        {"cmd": "易经历史", "desc": "查看自己的最近起卦记录。"},
        {"cmd": "易经记录 ID", "desc": "查看指定记录的完整长图。"},
        {"cmd": "随机一卦", "desc": "随机生成一个观察主题，不使用问题预处理和问题解读。"},
        {"cmd": "易经设置", "desc": "查看或修改本群配置。"},
        {"cmd": "易经设置 重复窗口 30", "desc": "设置短期相似问题检测窗口，单位分钟。"},
        {"cmd": "易经设置 历史窗口 120", "desc": "设置传给 LLM 预处理的近期历史窗口，单位分钟。"},
    ]
    await _finish_template(matcher, "help.html", {"commands": commands})


@cast_matcher.handle()
async def _cast(bot: Bot, event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    raw = get_plain_text(event)
    body = parse_command_body(raw, "起卦")
    if raw.strip().startswith("算卦") or raw.strip().startswith("/算卦"):
        body = parse_command_body(raw, "算卦")
    question, method = _parse_cast_body(body)
    if method == "manual":
        key = (get_group_id(event), get_user_id(event))
        _MANUAL_SESSIONS[key] = {"question": question, "stage": "method"}
        await _notice(
            matcher,
            "手动起卦引导",
            "请选择手动方式：\n1. 发送：铜钱\n2. 发送：大衍\n\n"
            "铜钱法随后请自下而上输入 6 组，每组 3 个正/反。\n"
            "大衍法可直接自下而上输入 6 个爻值：6 7 8 9。",
        )
    if not question:
        await _notice(matcher, "缺少问题", "请使用：起卦 你的问题\n例如：起卦 此行去山西实习一程怎么样")
    await _run_cast(matcher=matcher, bot=bot, event=event, session=session, question=question, method=method)


@query_matcher.handle()
async def _query(event: Event, matcher: Matcher) -> None:
    raw = get_plain_text(event)
    query = parse_command_body(raw, "解卦")
    if not query:
        await _notice(matcher, "缺少卦象", "请使用：解卦 需\n也可以输入卦序、卦名或符号。")
    parsed = await parse_hexagram_query(query)
    q = str(parsed.get("normalized_query") or parsed.get("query") or query)
    payload = build_hexagram_query_payload(q)
    if not payload.get("found", True):
        await _notice(matcher, "未找到卦象", f"未能识别：{query}\n请尝试输入卦名，如：乾、坤、需；或输入 1-64。")
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
    record = await get_record(session, record_id)
    if record is None:
        await _notice(matcher, "记录不存在", f"未找到记录：{record_id}")
    await _finish_template(matcher, "card.html", build_record_payload_from_dict(record_to_dict(record)))


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
                cfg.llm_enabled = parts[1] in {"开启", "启用", "on", "true", "1"}
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
    rows = [
        {"name": "群ID", "value": group_id},
        {"name": "是否启用", "value": "是" if cfg.enabled else "否"},
        {"name": "默认起卦方式", "value": "大衍" if cfg.default_method == "yarrow" else "铜钱"},
        {"name": "群冷却秒数", "value": cfg.cooldown_seconds},
        {"name": "用户24小时限额", "value": cfg.daily_limit},
        {"name": "重复问题窗口", "value": f"{cfg.duplicate_window_minutes} 分钟"},
        {"name": "LLM历史窗口", "value": f"{cfg.history_minutes_for_llm} 分钟"},
        {"name": "本群LLM解读", "value": "开启" if cfg.llm_enabled else "关闭"},
        {"name": "全局LLM配置", "value": "开启" if plugin_config.yijing_llm_enabled else "关闭"},
        {"name": "铜钱输入", "value": f"{plugin_config.yijing_positive_face}/{plugin_config.yijing_negative_face}"},
    ]
    await _finish_template(matcher, "settings.html", {"rows": rows})


_MANUAL_SESSIONS: dict[tuple[str, str], dict[str, Any]] = {}


async def _has_manual_session(event: Event) -> bool:
    return (get_group_id(event), get_user_id(event)) in _MANUAL_SESSIONS


manual_input_matcher = on_message(rule=Rule(_has_manual_session), block=True, priority=5)
manual_service.patch_matcher(manual_input_matcher)


@manual_input_matcher.handle()
async def _manual_input(bot: Bot, event: Event, matcher: Matcher, session: async_scoped_session) -> None:
    key = (get_group_id(event), get_user_id(event))
    state = _MANUAL_SESSIONS.get(key)
    if not state:
        return
    text = get_plain_text(event).strip()
    if text in {"取消", "退出", "停止"}:
        _MANUAL_SESSIONS.pop(key, None)
        await _notice(matcher, "已取消", "本次手动起卦已取消。")
    if state.get("stage") == "method":
        if text in {"铜钱", "硬币", "coin"}:
            state["stage"] = "values"
            state["method"] = "manual_coin"
            await _notice(
                matcher,
                "请输入铜钱结果",
                f"请自下而上输入 6 组，每组 3 个"
                f"{plugin_config.yijing_positive_face}/{plugin_config.yijing_negative_face}。\n"
                "示例：正反正 反反正 正正反 正反反 反正正 反反反",
            )
        if text in {"大衍", "蓍草", "yarrow"}:
            state["stage"] = "values"
            state["method"] = "manual_yarrow"
            await _notice(
                matcher,
                "请输入大衍结果",
                "请自下而上输入 6 个爻值，每个只能是 6/7/8/9。\n示例：7 8 9 6 7 8",
            )
        await _notice(matcher, "未识别方式", "请发送：铜钱 或 大衍。发送“取消”可退出。")
    method = str(state.get("method"))
    try:
        if method == "manual_coin":
            values = parse_manual_coin(text)
            groups = [g for g in text.replace("，", " ").replace(",", " ").split() if g]
            coins = [list(g) for g in groups]
        else:
            values = parse_manual_yarrow(text)
            coins = []
    except Exception as exc:  # noqa: BLE001
        await _notice(matcher, "输入格式错误", str(exc), "发送“取消”可退出手动起卦。")
    _MANUAL_SESSIONS.pop(key, None)
    await _run_cast(
        matcher=matcher,
        bot=bot,
        event=event,
        session=session,
        question=state.get("question") or None,
        method=method,
        manual_values=values,
        manual_coins=coins,
    )
